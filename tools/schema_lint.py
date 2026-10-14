#!/usr/bin/env python3
"""Schema linter of the pilot study: checks the result of an agent run against the rules.

    tools/schema_lint.py results/study-20261014-120000

For every run in <results>/runs.csv the migrations of the workspace are applied to a fresh
PostgreSQL database (a throw-away Docker container), the schema is read from the catalog and every
rule of the guidelines (DB-01 ... DES-09) is checked. Only the objects that the agent created or changed
are scored, the existing violations of the sample project are not counted against the agent.

Output: <results>/lint.csv (one row per run), <run_dir>/lint.json (every single check) and a summary.

Rule levels:
  DB, STD  the rules to follow; the rate is the share of satisfied rules
  DES      conflicting conventions; the rate shows how many of them the agent adopted

Several checks are heuristics (e.g. which column holds an enumeration); see the helpers below.
Requires Docker and Python >= 3.9, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

__version__ = "1.0.0"

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "sample_project"        # the unchanged sample project
NARROW_PROMPTS = {"urgent-fix"}               # tasks that change one spot of an existing table
GUIDELINES = ROOT / "sample_guidelines"   # the linter must cover the same rules
CONTAINER = "opencode-multirun-lint"
IMAGE = "postgres:17-alpine"
SOURCES = ("DB", "STD", "DES")

LINT_COLUMNS = (
    "batch_id", "run_index", "label", "harness", "model", "prompt", "status", "applied", "error", "touched",
    "db_applicable", "db_satisfied", "db_rate", "db_checks", "db_passed",
    "std_applicable", "std_satisfied", "std_rate", "std_checks", "std_passed",
    "des_applicable", "des_satisfied", "des_rate", "des_checks", "des_passed",
    "violations_baseline", "violations_result", "regressions", "failed_rules", "adopted_des", "run_dir",
)


# --------------------------------------------------------------------------- PostgreSQL

class Postgres:
    """A throw-away PostgreSQL in a Docker container."""

    def __init__(self) -> None:
        self.started = False

    def __enter__(self) -> "Postgres":
        subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)
        res = subprocess.run(["docker", "run", "-d", "--rm", "--name", CONTAINER, "-e", "POSTGRES_PASSWORD=lint",
                              IMAGE], capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"error: cannot start PostgreSQL: {res.stderr.strip()}")
        self.started = True
        stable = 0
        for _ in range(60):  # the image restarts the server once after its initialization
            ok = self.psql("postgres", "SELECT 1")[0]
            stable = stable + 1 if ok else 0
            if stable >= 3:
                return self
            time.sleep(1)
        sys.exit("error: PostgreSQL did not become ready")

    def __exit__(self, *exc: object) -> None:
        if self.started:
            subprocess.run(["docker", "stop", "-t", "1", CONTAINER], capture_output=True)

    def psql(self, db: str, sql: str) -> tuple[bool, str]:
        res = subprocess.run(["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres", "-d", db, "-X", "-q",
                              "-At", "-v", "ON_ERROR_STOP=1", "-f", "-"],
                             input=sql, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            return False, res.stderr.strip()
        return True, res.stdout

    def query_json(self, db: str, select: str) -> list[dict[str, Any]]:
        ok, out = self.psql(db, f"SELECT coalesce(json_agg(t), '[]'::json) FROM ({select}) t;")
        if not ok:
            raise RuntimeError(out)
        return json.loads(out)


CATALOG_QUERIES = {
    "tables": """SELECT c.relname AS name, obj_description(c.oid, 'pg_class') AS comment
                 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                 WHERE n.nspname = 'public' AND c.relkind = 'r' ORDER BY 1""",
    "columns": """SELECT c.relname AS "table", a.attname AS name, a.attnum AS pos,
                         format_type(a.atttypid, a.atttypmod) AS type, ty.typname, ty.typcategory AS typcat,
                         a.attnotnull AS notnull, a.attidentity AS identity,
                         pg_get_expr(d.adbin, d.adrelid) AS dflt, col_description(c.oid, a.attnum) AS comment
                  FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
                  JOIN pg_namespace n ON n.oid = c.relnamespace JOIN pg_type ty ON ty.oid = a.atttypid
                  LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
                  WHERE n.nspname = 'public' AND c.relkind = 'r' AND a.attnum > 0 AND NOT a.attisdropped
                  ORDER BY c.relname, a.attnum""",
    "constraints": """SELECT c.relname AS "table", co.conname AS name, co.contype AS type,
                             pg_get_constraintdef(co.oid) AS def, co.confdeltype AS ondelete, rc.relname AS ref,
                             (SELECT json_agg(a.attname ORDER BY k.ord)
                                FROM unnest(co.conkey) WITH ORDINALITY k(attnum, ord)
                                JOIN pg_attribute a ON a.attrelid = co.conrelid AND a.attnum = k.attnum) AS cols
                      FROM pg_constraint co JOIN pg_class c ON c.oid = co.conrelid
                      JOIN pg_namespace n ON n.oid = c.relnamespace LEFT JOIN pg_class rc ON rc.oid = co.confrelid
                      WHERE n.nspname = 'public' AND co.contype IN ('p', 'f', 'u', 'c') AND c.relkind = 'r'
                      ORDER BY c.relname, co.conname""",
    "indexes": """SELECT c.relname AS "table", i.relname AS name, ix.indisunique AS "unique",
                         (SELECT json_agg(a.attname ORDER BY k.ord)
                            FROM unnest(ix.indkey::int2[]) WITH ORDINALITY k(attnum, ord)
                            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
                            WHERE k.attnum > 0) AS cols,
                         pg_get_indexdef(ix.indexrelid) AS def,
                         ix.indisprimary AS pk,
                         EXISTS (SELECT 1 FROM pg_constraint co WHERE co.conindid = ix.indexrelid) AS by_constraint
                  FROM pg_index ix JOIN pg_class i ON i.oid = ix.indexrelid JOIN pg_class c ON c.oid = ix.indrelid
                  JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE n.nspname = 'public' AND c.relkind = 'r' ORDER BY c.relname, i.relname""",
    "views": """SELECT c.relname AS name, obj_description(c.oid, 'pg_class') AS comment,
                       pg_get_viewdef(c.oid) AS def,
                       (SELECT json_agg(a.attname ORDER BY a.attnum) FROM pg_attribute a
                         WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped) AS cols
                FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relkind IN ('v', 'm') ORDER BY 1""",
    "triggers": """SELECT t.tgname AS name, c.relname AS "table", c.relkind AS kind, p.prosrc AS src
                   FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_proc p ON p.oid = t.tgfoid
                   JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE NOT t.tgisinternal AND n.nspname = 'public' ORDER BY 1""",
}


# --------------------------------------------------------------------------- migrations

MIGRATION_NAME = re.compile(r"^V(\d+(?:[._]\d+)*)__[a-z0-9_]+\.sql$")


def read_sources(workspace: Path) -> dict[str, str]:
    """db/migrations/*.sql and db/scripts/*.sql of a workspace, by relative path."""
    out: dict[str, str] = {}
    for folder in ("db/migrations", "db/scripts"):
        for path in sorted((workspace / folder).glob("*.sql")):
            out[f"{folder}/{path.name}"] = path.read_text(encoding="utf-8", errors="replace")
    return out


def migration_order(path: str) -> Optional[tuple[int, ...]]:
    m = MIGRATION_NAME.match(Path(path).name)
    if not path.startswith("db/migrations/") or not m:
        return None
    return tuple(int(p) for p in re.split(r"[._]", m.group(1)))


def build_schema(pg: Postgres, name: str, files: dict[str, str]) -> tuple[Optional["Schema"], str]:
    """Apply the migrations to a fresh database and read the catalog. Returns (schema, error)."""
    db = "lint_" + name
    ok, err = pg.psql("postgres", f'CREATE DATABASE "{db}"')
    if not ok:
        return None, err
    try:
        ordered = sorted((p for p in files if migration_order(p)), key=lambda p: migration_order(p) or ())
        for path in ordered:
            ok, err = pg.psql(db, files[path])
            if not ok:
                first = next((ln for ln in err.splitlines() if "ERROR" in ln), err.splitlines()[0] if err else "failed")
                return None, f"{path}: {first.strip()}"
        data = {key: pg.query_json(db, sql) for key, sql in CATALOG_QUERIES.items()}
        return Schema(data, files), ""
    finally:
        pg.psql("postgres", f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')


# --------------------------------------------------------------------------- schema model

QUANTITY = re.compile(r"(weight|quantity|volume|height|length|width|distance|duration|interval|yield|liters|"
                      r"_kg|_cm|_days|_months|^age|_age|amount|dose)", re.I)
MONEY = re.compile(r"(price|cost|total|fee|salary|wage|payment|revenue|budget|_sum|_eur|_usd|_chf|_gbp)", re.I)
UNITS = ("kg", "g", "t", "liters", "l", "ml", "cm", "m", "mm", "days", "months", "years", "hours", "minutes", "percent")
CURRENCY_SUFFIX = ("_eur", "_usd", "_chf", "_gbp")
NUMERIC_TYPES = {"int2", "int4", "int8", "float4", "float8", "numeric"}
DATE_NAME = re.compile(r"(_date|_on|_at|Date|At)$|^(date|born|since|until)$")
ENUM_NAME = re.compile(r"(^|_)(type|status|phase|state|kind|category)$")
OPTIONAL_NAME = re.compile(r"(note|descr|comment|remark|diagnos|medicat|email|phone|mobile|city|street|"
                           r"_until$|_to$|^end_|deleted_|cancel)", re.I)
PII_NAME = re.compile(r"(^|_)(first_name|last_name|full_name|email|phone|mobile|street|postal_code|zip|city|address)"
                      r"($|_)", re.I)
PERSON_TABLES = {"customers", "employees", "veterinarians", "users", "persons", "contacts", "clients"}
SPECIES = {"horse", "cow", "donkey", "pig", "goat", "sheep", "rabbit", "chicken", "duck", "goose", "turkey"}
ANIMAL_CORE = {"name": ("varchar",), "birth_date": ("date",), "weight_kg": ("numeric",), "stable_id": ("int8",)}
DISCRIMINATORS = {"animal_type", "species", "type", "kind"}
DDL = re.compile(r"\b(create|alter|drop)\s+(or\s+replace\s+)?(unique\s+)?(table|index|view|trigger|function|type|"
                 r"schema|sequence|extension)\b", re.I)
DML = re.compile(r"\b(insert\s+into|update\s+[\w\".]+\s+set|delete\s+from)\b", re.I)


def singular(name: str) -> str:
    if name.endswith(("us", "is")):  # status, bonus
        return name
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith("sses"):
        return name[:-2]
    return name[:-1] if name.endswith("s") and not name.endswith("ss") else name


def is_plural(name: str) -> bool:
    last = name.split("_")[-1]
    return singular(last) != last or last in {"livestock", "sheep", "cattle", "poultry"}


def strip_sql(text: str) -> str:
    """The statements of a script without comments and dollar-quoted bodies."""
    text = re.sub(r"\$(\w*)\$.*?\$\1\$", " ", text, flags=re.S)
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"--[^\n]*", " ", text)


class Schema:
    """The catalog of a database plus the SQL files it was built from."""

    def __init__(self, data: dict[str, list[Any]], files: dict[str, str]) -> None:
        self.tables = {t["name"]: t for t in data["tables"]}
        self.cols: dict[str, list[dict]] = defaultdict(list)
        self.cons: dict[str, list[dict]] = defaultdict(list)
        self.idx: dict[str, list[dict]] = defaultdict(list)
        self.triggers: dict[str, list[dict]] = defaultdict(list)
        for col in data["columns"]:
            m = re.search(r"\((\d+)(?:,(\d+))?\)", col["type"])
            col["len"] = int(m.group(1)) if m else None
            col["scale"] = int(m.group(2)) if m and m.group(2) else None
            self.cols[col["table"]].append(col)
        for con in data["constraints"]:
            con["cols"] = con["cols"] or []
            self.cons[con["table"]].append(con)
        for ix in data["indexes"]:
            ix["cols"] = ix["cols"] or []
            self.idx[ix["table"]].append(ix)
        for trg in data["triggers"]:
            self.triggers[trg["table"]].append(trg)
        self.views = {v["name"]: v for v in data["views"]}
        self.files = files

    # constraints
    def fks(self, t: str) -> list[dict]:
        return [c for c in self.cons[t] if c["type"] == "f"]

    def pk(self, t: str) -> Optional[dict]:
        return next((c for c in self.cons[t] if c["type"] == "p"), None)

    def checks(self, t: str) -> list[dict]:
        return [c for c in self.cons[t] if c["type"] == "c"]

    def fk_cols(self, t: str) -> set[str]:
        return {col for fk in self.fks(t) for col in fk["cols"]}

    def pk_cols(self, t: str) -> set[str]:
        pk = self.pk(t)
        return set(pk["cols"]) if pk else set()

    def checked_cols(self, t: str) -> set[str]:
        return {col for c in self.checks(t) for col in c["cols"]}

    # column classes (heuristics on names and types)
    def plain_cols(self, t: str) -> list[dict]:
        """Columns without primary key, foreign keys and audit columns."""
        skip = self.pk_cols(t) | self.fk_cols(t)
        return [c for c in self.cols[t] if c["name"] not in skip and not is_audit(c["name"]) and c["name"] != "id"]

    def kind(self, t: str, col: dict) -> str:
        """'money', 'quantity' or '' for numeric columns that hold a money amount or a measured quantity."""
        if col["typname"] not in NUMERIC_TYPES or col not in self.plain_cols(t):
            return ""
        name = col["name"]
        if MONEY.search(name):
            return "money"
        return "quantity" if QUANTITY.search(name) else ""

    def kind_cols(self, t: str, kind: str) -> list[dict]:
        return [c for c in self.cols[t] if self.kind(t, c) == kind]

    def money_quantity_cols(self, t: str) -> list[dict]:
        return [c for c in self.cols[t] if self.kind(t, c)]

    def enum_cols(self, t: str) -> list[dict]:
        return [c for c in self.plain_cols(t) if ENUM_NAME.search(c["name"])
                and c["typname"] in NUMERIC_TYPES | {"varchar", "text", "bpchar"}]

    def flag_cols(self, t: str) -> list[dict]:
        return [c for c in self.plain_cols(t) if c["typname"] == "bool" or re.match(r"(is|has)[_A-Z]", c["name"])
                or (c["typname"] == "bpchar" and c["len"] == 1)]

    def date_cols(self, t: str) -> list[dict]:
        return [c for c in self.plain_cols(t) if DATE_NAME.search(c["name"]) or c["typname"] in ("date", "timestamp", "timestamptz")]

    def is_animal(self, t: str) -> bool:
        base = t[4:] if t.startswith("tbl_") else t
        names = {c["name"] for c in self.cols[t]}
        return singular(base) in SPECIES or base in ("small_livestock", "livestock") or len(names & set(ANIMAL_CORE)) >= 3

    def id_cols(self, t: str) -> list[str]:
        return [c["name"] for c in self.cols[t] if c["name"].endswith(("_id", "Id")) and c["name"] not in self.pk_cols(t)]

    def is_join(self, t: str) -> bool:
        ids = self.id_cols(t)
        return len(ids) >= 2 and len([c for c in self.cols[t] if c["name"] not in ids and c["name"] not in self.pk_cols(t)
                                      and not is_audit(c["name"])]) <= 1

    def is_reference(self, t: str) -> bool:
        return bool(re.search(r"(_types?|_status|_categories|_kinds?)$", t))

    def is_log(self, t: str) -> bool:
        return bool(re.search(r"(_log|_logs|_history|_events?)$", t))

    def sql_of(self, path: str) -> str:
        return strip_sql(self.files.get(path, ""))


def has_unit(name: str) -> bool:
    """True if the name ends with a unit: weight_kg, ageInMonths, liters."""
    for unit in UNITS:
        if name.lower().endswith(unit) and (len(name) == len(unit) or name[-len(unit) - 1] == "_" or name[-len(unit)].isupper()):
            return True
    return False


def is_audit(name: str) -> bool:
    return name in ("created_at", "updated_at", "createdAt", "updatedAt")


# --------------------------------------------------------------------------- rules

@dataclass
class Item:
    rule: str
    scope: str      # table:<name>, view:<name> or file:<path>
    obj: str
    ok: bool
    detail: str = ""

    def key(self) -> tuple[str, str, str]:
        return self.rule, self.scope, self.obj


RULES: dict[str, Callable[[Schema], list[Item]]] = {}


def rule(rule_id: str) -> Callable[[Callable[[Schema], list[Item]]], Callable[[Schema], list[Item]]]:
    def register(fn: Callable[[Schema], list[Item]]) -> Callable[[Schema], list[Item]]:
        RULES[rule_id] = fn
        return fn
    return register


def migrations(s: Schema) -> list[str]:
    return [p for p in s.files if p.startswith("db/migrations/")]


def scripts(s: Schema) -> list[str]:
    return [p for p in s.files if p.startswith("db/scripts/")]


# -- DB: base guideline

@rule("DB-01")
def db01(s: Schema) -> list[Item]:
    return [Item("DB-01", f"table:{t}", t, bool(re.fullmatch(r"[a-z][a-z0-9_]*", t)) and not t.startswith("tbl_")
                 and is_plural(t)) for t in s.tables]


@rule("DB-02")
def db02(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        pk = s.pk(t)
        col = next((c for c in s.cols[t] if pk and pk["cols"] == [c["name"]]), None)
        ok = bool(col and col["name"] == "id" and col["typname"] == "int8" and col["identity"] in ("a", "d"))
        out.append(Item("DB-02", f"table:{t}", t, ok, "" if ok else "primary key is not 'id BIGINT' identity"))
    return out


@rule("DB-03")
def db03(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        for fk in s.fks(t):
            ok = len(fk["cols"]) == 1 and fk["cols"][0].endswith("_id")
            out.append(Item("DB-03", f"table:{t}", f"{t}.{'+'.join(fk['cols'])}", ok, "foreign key column must end with _id"))
        for c in s.plain_cols(t):
            if c["name"].endswith("_id") and c["name"] not in s.fk_cols(t):
                out.append(Item("DB-03", f"table:{t}", f"{t}.{c['name']}", False, "id column without foreign key"))
    return out


@rule("DB-04")
def db04(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        for c in s.money_quantity_cols(t):
            if s.kind(t, c) == "money":
                ok = c["typname"] == "numeric" and c["scale"] == 2
            else:
                ok = c["typname"] not in ("float4", "float8")
            out.append(Item("DB-04", f"table:{t}", f"{t}.{c['name']}", ok, c["type"]))
    return out


@rule("DB-05")
def db05(s: Schema) -> list[Item]:
    return [Item("DB-05", f"table:{t}", f"{t}.{c['name']}",
                 c["typname"] in ("varchar", "text") and c["name"] in s.checked_cols(t), c["type"])
            for t in s.tables for c in s.enum_cols(t)]


@rule("DB-06")
def db06(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        loose = [c["name"] for c in s.cols[t] if not c["notnull"] and c["name"] not in s.fk_cols(t)
                 and not OPTIONAL_NAME.search(c["name"])]
        out.append(Item("DB-06", f"table:{t}", t, not loose, "nullable: " + ", ".join(loose) if loose else ""))
    return out


@rule("DB-07")
def db07(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        unique_sets = [set(c["cols"]) for c in s.cons[t] if c["type"] in ("p", "u")] + \
                      [set(i["cols"]) for i in s.idx[t] if i["unique"]]
        natural = [c["name"] for c in s.plain_cols(t) if re.search(r"(^|_)(number|code)$", c["name"])
                   and not re.search(r"(postal|zip|country)_code$", c["name"])]
        if t not in PERSON_TABLES and not s.is_animal(t) and "name" in [c["name"] for c in s.cols[t]]:
            natural.append("name")
        for col in natural:
            out.append(Item("DB-07", f"table:{t}", f"{t}.{col}", any(col in u for u in unique_sets)))
        if s.is_join(t):
            ids = set(s.id_cols(t))
            out.append(Item("DB-07", f"table:{t}", f"{t}:join", any(len(ids & u) >= 2 for u in unique_sets)))
    return out


@rule("DB-08")
def db08(s: Schema) -> list[Item]:
    return [Item("DB-08", f"table:{t}", f"{t}.{c['name']}", c["name"] in s.checked_cols(t))
            for t in s.tables for c in s.money_quantity_cols(t)]


@rule("DB-09")
def db09(s: Schema) -> list[Item]:
    return [Item("DB-09", f"table:{t}", f"{t}:{fk['name']}", fk["ondelete"] in ("r", "n"), f"on delete '{fk['ondelete']}'")
            for t in s.tables for fk in s.fks(t)]


@rule("DB-10")
def db10(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        if not s.is_animal(t):
            continue
        by_name = {c["name"]: c for c in s.cols[t]}
        missing = [n for n, types in ANIMAL_CORE.items() if n not in by_name or by_name[n]["typname"] not in types]
        shared = [c["name"] for c in s.cols[t] if c["name"] in DISCRIMINATORS]
        out.append(Item("DB-10", f"table:{t}", t, not missing and not shared,
                        ("differs: " + ", ".join(missing) if missing else "") + (" shared table" if shared else "")))
    return out


@rule("DB-11")
def db11(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        by_name = {c["name"]: c for c in s.cols[t]}
        ok = all(n in by_name and by_name[n]["notnull"] and by_name[n]["typname"] in ("timestamp", "timestamptz")
                 for n in ("created_at", "updated_at"))
        out.append(Item("DB-11", f"table:{t}", t, ok))
    return out


@rule("DB-12")
def db12(s: Schema) -> list[Item]:
    out = [Item("DB-12", f"file:{p}", p, bool(MIGRATION_NAME.match(Path(p).name)), "file name") for p in migrations(s)]
    out += [Item("DB-12", f"file:{p}", p, not DDL.search(s.sql_of(p)), "schema change outside of a migration")
            for p in scripts(s)]
    return out


# -- STD: additive standards

@rule("STD-01")
def std01(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        for fk in s.fks(t):
            n = len(fk["cols"])
            ok = any(i["cols"][:n] == fk["cols"] for i in s.idx[t])
            out.append(Item("STD-01", f"table:{t}", f"{t}.{'+'.join(fk['cols'])}", ok))
    return out


@rule("STD-02")
def std02(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        for c in s.cons[t]:
            if c["type"] == "u" and len(c["cols"]) > 1:
                out.append(Item("STD-02", f"table:{t}", f"{t}:{c['name']}", c["name"] == f"uq_{t}_" + "_".join(c["cols"])))
        for i in s.idx[t]:
            if not i["by_constraint"] and not i["pk"] and len(i["cols"]) > 1:
                prefix = "uq" if i["unique"] else "idx"
                out.append(Item("STD-02", f"table:{t}", f"{t}:{i['name']}", i["name"] in (f"{prefix}_{t}_" + "_".join(i["cols"]),
                                                                                         f"idx_{t}_" + "_".join(i["cols"]))))
    return out


@rule("STD-03")
def std03(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        out.append(Item("STD-03", f"table:{t}", t, bool(s.tables[t]["comment"]), "table comment"))
        notable = {c["name"] for c in s.enum_cols(t) + s.flag_cols(t)} | s.fk_cols(t) | \
                  {c["name"] for c in s.cols[t] if re.search(r"(^|_)code$", c["name"])}
        out += [Item("STD-03", f"table:{t}", f"{t}.{c['name']}", bool(c["comment"]), "column comment")
                for c in s.cols[t] if c["name"] in notable]
    return out


@rule("STD-04")
def std04(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        for c in s.cols[t]:
            if t in PERSON_TABLES and (PII_NAME.search(c["name"]) or c["name"] == "name"):
                out.append(Item("STD-04", f"table:{t}", f"{t}.{c['name']}", (c["comment"] or "").startswith("PII:")))
    for v, view in s.views.items():
        exposed = [c for c in view["cols"] if PII_NAME.search(c)]
        out.append(Item("STD-04", f"view:{v}", v, not exposed, "exposes " + ", ".join(exposed) if exposed else ""))
    return out


@rule("STD-05")
def std05(s: Schema) -> list[Item]:
    out = []
    for v in s.views:
        source = next((s.sql_of(p) for p in migrations(s) if re.search(rf"\bview\s+{re.escape(v)}\b", s.sql_of(p), re.I)), "")
        body = re.search(rf"\bview\s+{re.escape(v)}\b(.*?);", source, re.I | re.S)
        star = bool(body and re.search(r"select\s+(distinct\s+)?\*|\.\*", body.group(1), re.I))
        triggers = [t for t in s.triggers.values() for t in t if t["table"] == v]
        ok = bool(re.fullmatch(r"v_[a-z0-9_]+", v)) and not star and not triggers
        out.append(Item("STD-05", f"view:{v}", v, ok, "SELECT * " if star else ""))
    return out


@rule("STD-06")
def std06(s: Schema) -> list[Item]:
    return [Item("STD-06", f"table:{t}", f"{t}.{c['name']}", c["name"].startswith(("is_", "has_")))
            for t in s.tables for c in s.flag_cols(t)]


@rule("STD-07")
def std07(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        for c in s.date_cols(t):
            suffixes = {"date": ("_date", "_on"), "timestamp": ("_at",), "timestamptz": ("_at",)}.get(c["typname"], ("_date", "_on", "_at"))
            out.append(Item("STD-07", f"table:{t}", f"{t}.{c['name']}", c["name"].endswith(suffixes)))
    return out


@rule("STD-08")
def std08(s: Schema) -> list[Item]:
    return [Item("STD-08", f"table:{t}", f"{t}.{c['name']}", has_unit(c["name"]))
            for t in s.tables for c in s.kind_cols(t, "quantity")]


@rule("STD-09")
def std09(s: Schema) -> list[Item]:
    return [Item("STD-09", f"table:{t}", f"{t}.{c['name']}", c["name"].endswith(CURRENCY_SUFFIX))
            for t in s.tables for c in s.kind_cols(t, "money")]


@rule("STD-10")
def std10(s: Schema) -> list[Item]:
    out = []
    for p in migrations(s):
        sql = s.sql_of(p)
        out.append(Item("STD-10", f"file:{p}", p, not (DDL.search(sql) and DML.search(sql))))
    return out


@rule("STD-11")
def std11(s: Schema) -> list[Item]:
    out = []
    for p in migrations(s):
        first = next((ln.strip() for ln in s.files[p].splitlines() if ln.strip()), "")
        out.append(Item("STD-11", f"file:{p}", p, first.startswith("--") and len(first.strip("- ")) > 0))
    return out


# -- DES: conflicting conventions (adopted = True)

@rule("DES-01")
def des01(s: Schema) -> list[Item]:
    return [Item("DES-01", f"table:{t}", t, not is_plural(t) and not t.startswith("tbl_")) for t in s.tables]


@rule("DES-02")
def des02(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        pk = s.pk(t)
        col = next((c for c in s.cols[t] if pk and pk["cols"] == [c["name"]]), None)
        out.append(Item("DES-02", f"table:{t}", t, bool(col and col["name"] in (f"{t}_id", f"{singular(t)}_id")
                                                         and col["typname"] == "uuid")))
    return out


@rule("DES-03")
def des03(s: Schema) -> list[Item]:
    return [Item("DES-03", f"table:{t}", f"{t}.{c['name']}", not c["name"].startswith(("is_", "has_")))
            for t in s.tables for c in s.flag_cols(t)]


@rule("DES-04")
def des04(s: Schema) -> list[Item]:
    return [Item("DES-04", f"table:{t}", f"{t}.{c['name']}", not c["name"].endswith(CURRENCY_SUFFIX))
            for t in s.tables for c in s.kind_cols(t, "money")]


@rule("DES-05")
def des05(s: Schema) -> list[Item]:
    out = []
    for t in s.tables:
        out += [Item("DES-05", f"table:{t}", f"{t}.{c['name']}", False) for c in s.enum_cols(t)]
        out += [Item("DES-05", f"table:{t}", f"{t}.{c['name']}", True) for c in s.cols[t]
                if c["name"] in s.fk_cols(t) and ENUM_NAME.search(c["name"][:-3] if c["name"].endswith("_id") else "-")]
    return out


@rule("DES-06")
def des06(s: Schema) -> list[Item]:
    return [Item("DES-06", f"table:{t}", f"{t}:{fk['name']}", fk["ondelete"] == "c") for t in s.tables for fk in s.fks(t)]


@rule("DES-07")
def des07(s: Schema) -> list[Item]:
    return [Item("DES-07", f"table:{t}", t, any(c["name"] in DISCRIMINATORS for c in s.cols[t])) for t in s.tables if s.is_animal(t)]


@rule("DES-08")
def des08(s: Schema) -> list[Item]:
    return [Item("DES-08", f"table:{t}", t, not any(is_audit(c["name"]) for c in s.cols[t]))
            for t in s.tables if s.is_join(t) or s.is_reference(t) or s.is_log(t)]


@rule("DES-09")
def des09(s: Schema) -> list[Item]:
    return [Item("DES-09", f"file:{p}", p, bool(re.search(r"[A-Z]{2,}-\d+|ticket\s*#?\w+|#\d+", s.files[p], re.I)))
            for p in scripts(s)]


def run_rules(s: Schema) -> list[Item]:
    return [item for fn in RULES.values() for item in fn(s)]


# --------------------------------------------------------------------------- scoring

def signatures(s: Schema) -> dict[str, str]:
    """A fingerprint for every table, view and SQL file; used to find what an agent created or changed."""
    out: dict[str, str] = {}
    for t, table in s.tables.items():
        parts = [table["comment"], s.cols[t], [(c["name"], c["def"]) for c in s.cons[t]],
                 [(i["name"], i["def"]) for i in s.idx[t]], [(g["name"], g["src"]) for g in s.triggers[t]]]
        out[f"table:{t}"] = hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()
    for v, view in s.views.items():
        out[f"view:{v}"] = hashlib.sha1(json.dumps([view["def"], view["comment"]]).encode()).hexdigest()
    for p, text in s.files.items():
        out[f"file:{p}"] = hashlib.sha1(text.encode()).hexdigest()
    return out


def failing(items: list[Item], sources: tuple[str, ...] = ("DB", "STD")) -> set[tuple[str, str, str]]:
    return {i.key() for i in items if not i.ok and i.rule.split("-")[0] in sources}


def score(base: Schema, base_items: list[Item], result: Schema, narrow: bool = False) -> dict[str, Any]:
    """Compare the schema of a run with the baseline and score the objects that were created or changed.
    With `narrow` only the checks that are new or have a different result than before are scored."""
    base_sig, result_sig = signatures(base), signatures(result)
    touched = {scope for scope, sig in result_sig.items() if base_sig.get(scope) != sig}
    items = run_rules(result)
    scored = [i for i in items if i.scope in touched]
    if narrow:  # a targeted change: do not hold the agent responsible for what the object already had
        before = {i.key(): i.ok for i in base_items}
        scored = [i for i in scored if before.get(i.key()) != i.ok]
    row: dict[str, Any] = {"touched": len(touched)}
    failed_rules: set[str] = set()
    adopted: set[str] = set()
    for source in SOURCES:
        by_rule: dict[str, list[Item]] = defaultdict(list)
        for item in scored:
            if item.rule.startswith(source + "-"):
                by_rule[item.rule].append(item)
        satisfied = {r for r, group in by_rule.items() if all(i.ok for i in group)}
        if source == "DES":
            adopted = satisfied
        else:
            failed_rules |= set(by_rule) - satisfied
        n_checks = sum(len(g) for g in by_rule.values())
        passed = sum(1 for g in by_rule.values() for i in g if i.ok)
        low = source.lower()
        row[f"{low}_applicable"] = len(by_rule)
        row[f"{low}_satisfied"] = len(satisfied)
        row[f"{low}_rate"] = f"{len(satisfied) / len(by_rule):.3f}" if by_rule else ""
        row[f"{low}_checks"] = n_checks
        row[f"{low}_passed"] = passed
    base_failing = failing(base_items)
    result_failing = failing(items)
    ok_before = {i.key() for i in base_items if i.ok and i.rule.split("-")[0] in ("DB", "STD")}
    row["violations_baseline"] = len(base_failing)
    row["violations_result"] = len(result_failing)
    row["regressions"] = len(result_failing & ok_before)
    row["failed_rules"] = ";".join(sorted(failed_rules))
    row["adopted_des"] = ";".join(sorted(adopted))
    row["_items"] = [i.__dict__ for i in scored]
    return row


# --------------------------------------------------------------------------- main

def verify_rule_coverage(guidelines: Path) -> None:
    ids = set()
    for path in guidelines.glob("*.md"):
        ids |= set(re.findall(r"^- \*\*([A-Z]+-\d+) ", path.read_text(encoding="utf-8"), re.M))
    if ids != set(RULES):
        sys.exit(f"error: the linter and {guidelines} do not have the same rules "
                 f"(only in guidelines: {sorted(ids - set(RULES))}, only in linter: {sorted(set(RULES) - ids)})")


def summarize(rows: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["prompt"], f"{row['harness']}/{row['model'].split('/')[-1]}", row["label"])].append(row)

    def mean(values: list[float]) -> str:
        return f"{statistics.mean(values):.2f}" if values else "-"

    print(f"\n{'prompt':<16}{'harness/model':<28}{'scenario':<19}{'runs':>5}{'applied':>8}{'DB':>7}{'STD':>7}{'DES':>7}{'regr':>6}{'viol.':>7}")
    for (prompt, model, label), group in sorted(groups.items()):
        applied = [r for r in group if r["applied"] == 1 and r["touched"]]
        rates = {k: [float(r[f"{k}_rate"]) for r in applied if r[f"{k}_rate"] != ""] for k in ("db", "std", "des")}
        regr = mean([float(r["regressions"]) for r in applied])
        viol = mean([float(r["violations_result"]) for r in applied])
        print(f"{prompt:<16}{model:<28}{label:<19}{len(group):>5}{sum(r['applied'] == 1 for r in group):>8}"
              f"{mean(rates['db']):>7}{mean(rates['std']):>7}{mean(rates['des']):>7}{regr:>6}{viol:>7}")
    print("\nDB, STD: share of satisfied rules on the new or changed objects; DES: share of adopted conflicting rules;"
          "\nregr: rules that were fine before and are violated now; viol.: violations of DB and STD in the whole schema.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the results of a study against the rules.")
    parser.add_argument("results", type=Path, help="results directory with runs.csv")
    args = parser.parse_args()

    runs_csv = args.results / "runs.csv"
    if not runs_csv.exists():
        sys.exit(f"error: {runs_csv} not found")
    verify_rule_coverage(GUIDELINES)
    with runs_csv.open(newline="", encoding="utf-8") as fh:
        runs = list(csv.DictReader(fh))

    rows: list[dict[str, Any]] = []
    with Postgres() as pg:
        base, error = build_schema(pg, "baseline", read_sources(BASELINE))
        if base is None:
            sys.exit(f"error: the baseline does not apply: {error}")
        base_items = run_rules(base)
        for n, run in enumerate(runs):
            run_dir = Path(run["run_dir"])
            workspace = run_dir / "workspace"
            row: dict[str, Any] = {k: run.get(k, "") for k in ("batch_id", "run_index", "label", "prompt", "status", "run_dir")}
            row["model"] = run.get("model_effective") or run.get("model_requested", "")
            row["harness"] = run.get("harness") or "opencode"
            if not workspace.is_dir():
                continue
            schema, error = build_schema(pg, f"run{n}", read_sources(workspace))
            row["applied"] = int(schema is not None)
            row["error"] = error
            result = score(base, base_items, schema, run["prompt"] in NARROW_PROMPTS) if schema else {"touched": 0}
            items = result.pop("_items", [])
            row.update(result)
            (run_dir / "lint.json").write_text(json.dumps({"error": error, "items": items}, indent=1), encoding="utf-8")
            rows.append(row)
            print(f"{run['label']:<19} {run['prompt']:<16} run {run['run_index']:>3}: "
                  f"{'applied' if schema else 'FAILED: ' + error}")

    out = args.results / "lint.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LINT_COLUMNS, restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n{len(rows)} runs checked, written to {out}")
    summarize(rows)


if __name__ == "__main__":
    main()
