#!/usr/bin/env python3
"""Builds the knowledge scenarios of the pilot study from the guidelines in sample_guidelines/.

    study/build-scenarios.py

Every scenario is a directory in study/scenarios/ whose content is copied into the workspace of the
agent (see study/run.sh). The documents of the MCP servers are written to study/scenarios/mcp-*.
The directory is rebuilt from scratch, do not edit it by hand.

All scenarios carry the same 50 rules; only the form and the channel differ:

    baseline          no knowledge
    a-agents-md       all guidelines inside AGENTS.md
    b-guideline-files the three guideline files in guidelines/
    c-spec-files      the rules grouped by requirement, one spec per capability in specs/ (spec-driven)
    d-mcp-server      the three guideline files through an MCP server
    e-mcp-and-specs   static rules (naming, data types) through an MCP server,
              dynamic rules (everything else) as specs in specs/
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDELINES = ROOT / "sample_guidelines"
OUT = ROOT / "study" / "scenarios"
BASE_CONFIG = ROOT / "study" / "config" / "opencode.json"

RULE_LINE = re.compile(r"^- \*\*(?P<id>[A-Z]+-\d+) (?P<title>.+?)\*\*\s*(?P<text>.*)$")

# capability -> (title, purpose, static). Static capabilities are conventions that rarely change; they
# go to the MCP server in the scenario "e-mcp-and-specs". The dynamic ones are requirements that depend on the
# task at hand and live next to the code as specs.
CAPABILITIES = {
    "naming": ("Naming", "How tables, columns, keys, constraints, indexes and flags are named.", True),
    "data-types": ("Data types", "Which column type is used for which kind of value.", True),
    "integrity": ("Integrity", "Keys, relations, nullability and constraints.", False),
    "modeling": ("Modeling", "Structure of the tables and their audit information.", False),
    "database-objects": ("Database objects", "Indexes, documentation, views and triggers.", False),
    "migrations": ("Migrations", "How the schema is created and changed.", False),
}

CAPABILITY_OF = {
    "naming": "DB-01 DB-02 DB-03 DB-04 DB-05 DB-06 STD-02 STD-07 STD-08 STD-09 STD-10 DES-01 DES-02 DES-03 DES-04",
    "data-types": "DB-07 DB-08 DB-09 DB-10 DB-11 DES-07 DES-08 DES-09 DES-10 DES-11",
    "integrity": "DB-12 DB-13 DB-14 DB-15 DB-16 DB-19 DES-05 DES-06 DES-12 DES-13 DES-14",
    "modeling": "DB-17 DB-18 DES-15 DES-16",
    "database-objects": "STD-01 STD-03 STD-04 STD-05 STD-06",
    "migrations": "DB-20 DB-21 STD-11 STD-12 DES-17",
}

POINTER_FILES = (
    "# Project notes\n\n"
    "The database guidelines of this project are in the `guidelines/` directory. "
    "Read them before you work on the database and follow them.\n"
)
POINTER_SPECS = (
    "# Project notes\n\n"
    "The requirements for the database of this project are specified in the `specs/` directory, "
    "one `spec.md` per capability (`specs/<capability>/spec.md`). "
    "Read the specs that are relevant for your task before you work on the database and follow them.\n"
)
POINTER_MCP = (
    "# Project notes\n\n"
    "The database guidelines of this project are provided by the `docs` MCP server (library `guidelines`). "
    "Search them with its tools before you work on the database and follow them.\n"
)
POINTER_HYBRID = (
    "# Project notes\n\n"
    "The requirements for the database of this project come from two sources. "
    "The naming and data type conventions are provided by the `docs` MCP server (library `guidelines`); "
    "search them with its tools. All other requirements are specified in the `specs/` directory, "
    "one `spec.md` per capability (`specs/<capability>/spec.md`). "
    "Read the relevant parts of both before you work on the database and follow them.\n"
)


@dataclass
class Rule:
    id: str
    title: str
    text: str
    line: str
    sentence: str = ""
    capability: str = ""


def read_env() -> dict[str, str]:
    env = dict(os.environ)
    path = ROOT / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = raw.partition("=")
            if sep and not key.strip().startswith("#"):
                env.setdefault(key.strip(), value.strip())
    return env


def guideline_files() -> list[Path]:
    """The guideline files in the order base, standards, design conventions."""
    return [GUIDELINES / name for name in
            ("database-guidelines.md", "database-standards.md", "database-design-conventions.md")]


def parse_rules() -> list[Rule]:
    rules: list[Rule] = []
    for path in guideline_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = RULE_LINE.match(line)
            if m:
                rules.append(Rule(m["id"], m["title"].rstrip("."), m["text"], line,
                                  f"{m['title']} {m['text']}".strip()))
    capability = {rid: cap for cap, ids in CAPABILITY_OF.items() for rid in ids.split()}
    by_id = {r.id: r for r in rules}
    if sorted(capability) != sorted(by_id) or len(by_id) != len(rules):
        missing = sorted(set(by_id) - set(capability))
        extra = sorted(set(capability) - set(by_id))
        sys.exit(f"error: rules and capabilities do not match (unassigned: {missing}, unknown: {extra})")
    for rule in rules:
        rule.capability = capability[rule.id]
    return rules


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def config_json(mcp_port: str = "") -> str:
    config = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    if mcp_port:
        config["mcp"] = {"docs": {"type": "remote", "url": f"http://localhost:{mcp_port}/mcp", "enabled": True}}
    return json.dumps(config, indent=2) + "\n"


def spec_md(capability: str, rules: list[Rule]) -> str:
    title, purpose, _ = CAPABILITIES[capability]
    out = [f"# {title} Specification", "", "## Purpose", "", purpose, "", "## Requirements", ""]
    for rule in rules:
        out += [f"### Requirement: {rule.id} {rule.title}", "", rule.sentence, ""]
    return "\n".join(out)


def rules_md(capability: str, rules: list[Rule]) -> str:
    return "\n".join([f"# {CAPABILITIES[capability][0]}", ""] + [r.line for r in rules]) + "\n"


def main() -> None:
    env = read_env()
    port_full = env.get("DOCS_MCP_PORT", "6281")
    port_static = env.get("DOCS_MCP_STATIC_PORT", "6282")
    rules = parse_rules()
    by_capability = {cap: [r for r in rules if r.capability == cap] for cap in CAPABILITIES}
    static = [cap for cap, (_, _, is_static) in CAPABILITIES.items() if is_static]
    dynamic = [cap for cap in CAPABILITIES if cap not in static]
    files = guideline_files()

    if OUT.exists():
        shutil.rmtree(OUT)

    write(OUT / "baseline" / "opencode.json", config_json())

    write(OUT / "a-agents-md" / "opencode.json", config_json())
    documents = "\n".join(p.read_text(encoding="utf-8").rstrip("\n") + "\n" for p in files)
    write(OUT / "a-agents-md" / "AGENTS.md", "# Project notes\n\nThe database guidelines of this project follow.\n\n" + documents)

    write(OUT / "b-guideline-files" / "opencode.json", config_json())
    write(OUT / "b-guideline-files" / "AGENTS.md", POINTER_FILES)
    for path in files:
        write(OUT / "b-guideline-files" / "guidelines" / path.name, path.read_text(encoding="utf-8"))

    write(OUT / "c-spec-files" / "opencode.json", config_json())
    write(OUT / "c-spec-files" / "AGENTS.md", POINTER_SPECS)
    for cap, cap_rules in by_capability.items():
        write(OUT / "c-spec-files" / "specs" / cap / "spec.md", spec_md(cap, cap_rules))

    write(OUT / "d-mcp-server" / "opencode.json", config_json(port_full))
    write(OUT / "d-mcp-server" / "AGENTS.md", POINTER_MCP)

    write(OUT / "e-mcp-and-specs" / "opencode.json", config_json(port_static))
    write(OUT / "e-mcp-and-specs" / "AGENTS.md", POINTER_HYBRID)
    for cap in dynamic:
        write(OUT / "e-mcp-and-specs" / "specs" / cap / "spec.md", spec_md(cap, by_capability[cap]))
    for cap in static:
        write(OUT / "mcp-static" / f"{cap}.md", rules_md(cap, by_capability[cap]))

    write(OUT / "README.md",
          "Generated by `study/build-scenarios.py` from `sample_guidelines/`. Do not edit.\n\n"
          "Each directory with a scenario name is copied into the workspace of the agent. "
          "`mcp-static/` holds the documents of the MCP server of the scenario `e-mcp-and-specs`; "
          "the MCP server of `d-mcp-server` indexes `sample_guidelines/`.\n")

    print(f"{len(rules)} rules; static: {sum(len(by_capability[c]) for c in static)}, "
          f"dynamic: {sum(len(by_capability[c]) for c in dynamic)}")
    print(f"scenarios written to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
