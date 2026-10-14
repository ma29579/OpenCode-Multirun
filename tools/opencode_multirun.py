#!/usr/bin/env python3
"""OpenCode-Multirun: run one prompt several times with OpenCode and measure each run.

Every run works on its own copy of the working directory, so the runs are independent and
the original is never changed. OpenCode runs with an empty configuration directory, so that
the personal configuration of the user does not influence the study. For each run the script records quantitative metrics
(tokens, cost, duration, tool calls, size of the changes) in a CSV file and keeps the raw
data (event stream, answer text, patch of the changes) for later analysis.

Example:
  tools/opencode_multirun.py -f study/prompts/review-schema.md -n 5 \\
      -m github-copilot/claude-sonnet-5 -w sample_project --label base \\
      --add sample_guidelines/database-guidelines.md:guidelines/

Requirements: Python >= 3.9 (standard library only), opencode 2.x, git. Linux, macOS or WSL2.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn, Optional, Sequence

__version__ = "4.3.0"

# Columns of the result file. Changing them breaks existing result files, so a new study
# should start with a new output directory.
CSV_COLUMNS = (
    "batch_id", "run_index", "label", "prompt", "model_requested", "model_effective",
    "start_utc", "end_utc", "duration_s", "status", "exit_code", "error_message",
    "steps", "tokens_total", "tokens_input", "tokens_output", "tokens_reasoning",
    "tokens_cache_read", "tokens_cache_write", "cost_usd", "accounting_source",
    "tool_calls", "tool_errors", "mcp_calls", "tools_used", "output_chars",
    "sql_files_read", "guideline_files_read", "knowledge_accessed",
    "files_changed", "lines_added", "lines_deleted",
    "session_id", "prompt_sha256", "opencode_version", "run_dir",
)

STATUS_OK, STATUS_ERROR, STATUS_TIMEOUT = "ok", "error", "timeout"
SOURCE_STREAM, SOURCE_EXPORT, SOURCE_NONE = "stream", "export", "none"

EXIT_TIMEOUT = 124          # same as GNU "timeout"
EXIT_NOT_STARTED = 127      # the program could not be started (shell convention)
TIMEOUT_SEC = 1800  # protects against runs that hang, e.g. on a permission prompt
KILL_GRACE_SEC = 10         # wait between SIGTERM and SIGKILL
HELPER_TIMEOUT_SEC = 120    # version query, export, git
ERROR_MESSAGE_CHARS = 300
MCP_CALL = re.compile(r"\btools\.(\w+)\.(\w+)")
GUIDELINE_FILE = re.compile(r"^(?:\./)?(?:guidelines|specs)/.+\.md$")


# --------------------------------------------------------------------------- helpers

def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", file=sys.stderr, flush=True)


def fail(msg: str) -> NoReturn:
    log(f"ERROR: {msg}")
    sys.exit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def one_line(text: str, max_len: int) -> str:
    s = " ".join(text.split())
    return s[:max_len] + "…" if len(s) > max_len else s


def is_number(value: Any) -> bool:
    """True for int/float, but not for bool (an int subclass in Python)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def num(value: Any) -> float:
    return value if is_number(value) else 0


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def env_for(cwd: Path, config_home: Optional[Path] = None) -> dict[str, str]:
    """Environment for a process that runs in `cwd`.
    - OpenCode takes its project directory from PWD and not from the real working directory,
      so PWD must be set as well. Otherwise it would work in the directory this script started in.
    - config_home replaces ~/.config, so that the personal OpenCode configuration (MCP servers,
      plugins, rules) of the user does not leak into the study. Settings that other tools
      pass through OPENCODE_* variables are removed for the same reason."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")}
    env["PWD"] = str(cwd)
    if config_home is not None:
        env["XDG_CONFIG_HOME"] = str(config_home)
    return env


def run_quiet(cmd: Sequence[str], cwd: Optional[Path] = None,
              env: Optional[dict[str, str]] = None) -> Optional[subprocess.CompletedProcess]:
    """Run a helper command without a terminal; None if it cannot be run."""
    try:
        return subprocess.run(list(cmd), cwd=cwd, env=env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=HELPER_TIMEOUT_SEC)
    except (OSError, subprocess.SubprocessError):
        return None


# --------------------------------------------------------------------------- metrics

@dataclass
class Usage:
    """Token and cost values summed over all steps of a run."""
    steps: int = 0
    tokens_total: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_reasoning: int = 0
    tokens_cache_read: int = 0
    tokens_cache_write: int = 0
    cost_usd: float = 0.0

    @classmethod
    def from_parts(cls, parts: Sequence[dict]) -> Usage:
        """Sum up the step-finish parts. If "tokens.total" is missing it is computed
        from the single values (OpenCode counts cache tokens in "total")."""
        u = cls(steps=len(parts))
        for p in parts:
            tok = as_dict(p.get("tokens"))
            cache = as_dict(tok.get("cache"))
            t_in, t_out, t_rea = num(tok.get("input")), num(tok.get("output")), num(tok.get("reasoning"))
            c_read, c_write = num(cache.get("read")), num(cache.get("write"))
            total = tok["total"] if is_number(tok.get("total")) else t_in + t_out + t_rea + c_read + c_write
            u.tokens_total += int(total)
            u.tokens_input += int(t_in)
            u.tokens_output += int(t_out)
            u.tokens_reasoning += int(t_rea)
            u.tokens_cache_read += int(c_read)
            u.tokens_cache_write += int(c_write)
            u.cost_usd += float(num(p.get("cost")))
        return u


@dataclass
class StreamStats:
    """What can be read from the NDJSON event stream of one run."""
    session_id: str = ""
    usage: Usage = field(default_factory=Usage)
    tool_calls: int = 0
    tool_errors: int = 0
    mcp_calls: int = 0
    tools_used: set[str] = field(default_factory=set)
    files_read: set[str] = field(default_factory=set)
    error_events: int = 0
    error_message: str = ""
    texts: list[str] = field(default_factory=list)


def error_text(err: Any) -> str:
    """Readable message of an "error" event; its structure varies between versions."""
    if isinstance(err, dict):
        data = as_dict(err.get("data"))
        return str(data.get("message") or err.get("message") or json.dumps(err, ensure_ascii=False))
    return "" if err is None else str(err)


def parse_events(path: Path) -> StreamStats:
    """Evaluate the output of "opencode run --format json" (one JSON object per line).
    Lines that are not JSON objects are skipped, which keeps the evaluation robust."""
    st = StreamStats()
    step_parts: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return st
    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        if not st.session_id and isinstance(ev.get("sessionID"), str):
            st.session_id = ev["sessionID"]
        part, kind = as_dict(ev.get("part")), ev.get("type")
        if kind == "step_finish":
            step_parts.append(part)
        elif kind == "tool_use":
            st.tool_calls += 1
            if isinstance(part.get("tool"), str):
                st.tools_used.add(part["tool"])
            state = as_dict(part.get("state"))
            if state.get("status") == "error":
                st.tool_errors += 1
            if part.get("tool") == "read":
                path = as_dict(state.get("input")).get("path")
                if isinstance(path, str) and Path(path).suffix:  # a directory listing is not a read file
                    st.files_read.add(path)
            if part.get("tool") == "execute":  # OpenCode 2 calls MCP tools from code: tools.<server>.<tool>(...)
                for server, name in MCP_CALL.findall(str(as_dict(state.get("input")).get("code") or "")):
                    st.mcp_calls += 1
                    st.tools_used.add(f"{server}.{name}")
        elif kind == "error":
            st.error_events += 1
            st.error_message = st.error_message or error_text(ev.get("error"))
        elif kind == "text" and part.get("text"):
            st.texts.append(str(part["text"]))
    st.usage = Usage.from_parts(step_parts)
    return st


def read_export(session_id: str, cwd: Path, target: Path,
                env: dict[str, str]) -> tuple[Optional[Usage], str]:
    """Read the stored session with "opencode session export": it lists every model call of the
    agent with its tokens and cost. The output is written straight to a file, because through a
    pipe it can be cut off. Returns (usage or None, model actually used)."""
    try:
        with target.open("wb") as f:
            subprocess.run(["opencode", "session", "export", "--standalone", session_id], cwd=cwd, env=env,
                           stdout=f, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                           timeout=HELPER_TIMEOUT_SEC)
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, subprocess.SubprocessError):
        return None, ""
    start = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("{")), None)
    if start is None:  # there may be a text line before the JSON
        return None, ""
    raw = "\n".join(lines[start:])
    target.write_text(raw, encoding="utf-8")
    try:
        messages = as_dict(json.loads(raw)).get("messages")
    except json.JSONDecodeError:
        return None, ""
    steps = [m for m in messages if isinstance(m, dict) and m.get("type") == "assistant"] if isinstance(messages, list) else []
    usage = Usage.from_parts([{"tokens": m.get("tokens"), "cost": m.get("cost")} for m in steps])
    model = next((f"{as_dict(m.get('model')).get('providerID')}/{as_dict(m.get('model')).get('id')}"
                  for m in steps if as_dict(m.get("model")).get("id")), "")
    return usage, model


# --------------------------------------------------------------------------- workspace

def parse_add(spec: str) -> tuple[Path, str]:
    """"SRC" or "SRC:DEST". DEST is relative to the workspace; if it ends with "/" the
    source is copied into that directory under its own name."""
    src, _, dest = spec.partition(":")
    path = Path(src)
    if not path.exists():
        fail(f"--add: {src} does not exist")
    return path, dest or path.name


def create_workspace(workdir: Path, target: Path, adds: Sequence[tuple[Path, str]],
                     exclude: Path) -> None:
    """Copy the working directory and put the extra files into it. The output directory is
    left out if it lies inside the working directory, otherwise the agent would see old results."""
    shutil.copytree(workdir, target, symlinks=True,
                    ignore=lambda d, names: [n for n in names if (Path(d) / n).resolve() == exclude])
    for src, dest in adds:
        out = target / dest
        if dest.endswith("/"):
            out.mkdir(parents=True, exist_ok=True)
            out = out / src.name
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, out, symlinks=True, dirs_exist_ok=True)
        else:
            shutil.copy2(src, out)


def git(workspace: Path, *args: str) -> Optional[subprocess.CompletedProcess]:
    return run_quiet(["git", "-c", "user.name=multirun", "-c", "user.email=multirun@localhost",
                      "-c", "commit.gpgsign=false", *args], cwd=workspace, env=env_for(workspace))


def commit_baseline(workspace: Path) -> bool:
    """Record the starting state (including the added files) so that the changes of the
    agent can be measured. Works for directories with and without a git repository."""
    if not (workspace / ".git").exists() and (git(workspace, "init", "-q") is None):
        return False
    git(workspace, "add", "-A")
    res = git(workspace, "commit", "-q", "--allow-empty", "-m", "baseline")
    return res is not None and res.returncode == 0


def collect_changes(workspace: Path, patch_path: Path) -> tuple[str, str, str]:
    """Save the changes of the agent as a patch and return (files, lines added, lines deleted).
    Empty strings if git is not available."""
    if git(workspace, "add", "-A") is None:
        return "", "", ""
    numstat = git(workspace, "diff", "--cached", "--numstat", "HEAD")
    patch = git(workspace, "diff", "--cached", "HEAD")
    if numstat is None or patch is None or numstat.returncode != 0:
        return "", "", ""
    patch_path.write_text(patch.stdout, encoding="utf-8")
    files = added = deleted = 0
    for line in numstat.stdout.splitlines():
        cols = line.split("\t")
        files += 1
        if len(cols) >= 2 and cols[0].isdigit() and cols[1].isdigit():  # binary files show "-"
            added += int(cols[0])
            deleted += int(cols[1])
    return str(files), str(added), str(deleted)


# --------------------------------------------------------------------------- process

def terminate_group(proc: subprocess.Popen) -> None:
    """Stop the process and all its children: SIGTERM first, SIGKILL after a grace period."""
    for sig, grace in ((signal.SIGTERM, KILL_GRACE_SEC), (signal.SIGKILL, None)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=grace)
            return
        except subprocess.TimeoutExpired:
            continue


def run_process(cmd: Sequence[str], cwd: Path, env: dict[str, str], stdout_path: Path,
                stderr_path: Path, timeout: int) -> tuple[int, bool]:
    """Run the command and wait. stdin is /dev/null so that OpenCode never waits for input.
    The command gets its own process group so that a timeout or Ctrl+C stops the whole tree.
    Returns (exit code, timed out)."""
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        try:
            proc = subprocess.Popen(list(cmd), cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=out, stderr=err, start_new_session=True)
        except OSError as e:
            err.write(f"Could not start process: {e}\n".encode())
            return EXIT_NOT_STARTED, False
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            terminate_group(proc)
            return EXIT_TIMEOUT, True
        except KeyboardInterrupt:
            terminate_group(proc)
            raise
    return (128 - rc if rc < 0 else rc), False  # killed by signal N -> 128 + N (shell convention)


# --------------------------------------------------------------------------- one run

@dataclass(frozen=True)
class Batch:
    """Values that are the same for all runs of one invocation."""
    id: str
    dir: Path
    csv_path: Path
    workdir: Path
    cmd: list[str]
    prompt_name: str
    prompt_sha256: str
    opencode_version: str


def execute_run(i: int, args: argparse.Namespace, batch: Batch) -> dict[str, Any]:
    run_dir = batch.dir / f"run-{i:03d}"
    run_dir.mkdir(parents=True)
    workspace = run_dir / "workspace"
    try:
        create_workspace(batch.workdir, workspace, args.add_specs, args.out.resolve())
    except (OSError, shutil.Error) as e:
        fail(f"Could not create the workspace: {e}")
    has_baseline = commit_baseline(workspace)
    (run_dir / "command.txt").write_text(shlex.join(batch.cmd) + "\n", encoding="utf-8")
    log(f"Run {i}/{args.runs} started …")

    # An empty configuration directory outside of the workspace: OpenCode only sees what the study provides.
    config_home = run_dir / "opencode-config"
    config_home.mkdir()
    env = env_for(workspace, config_home)
    start_iso, t0 = now_iso(), time.perf_counter()
    exit_code, timed_out = run_process(batch.cmd, workspace, env, run_dir / "events.jsonl",
                                       run_dir / "stderr.log", TIMEOUT_SEC)
    duration = time.perf_counter() - t0
    end_iso = now_iso()

    st = parse_events(run_dir / "events.jsonl")
    usage, source, model_effective = st.usage, SOURCE_STREAM, ""
    if st.session_id:
        exported, model_effective = read_export(st.session_id, workspace, run_dir / "export.json", env)
        if exported and exported.steps >= max(1, usage.steps):
            usage, source = exported, SOURCE_EXPORT
    if usage.steps == 0:
        source = SOURCE_NONE

    answer = "\n\n".join(st.texts)
    (run_dir / "response.txt").write_text(answer, encoding="utf-8")
    changes = collect_changes(workspace, run_dir / "changes.patch") if has_baseline else ("", "", "")

    # OpenCode reports absolute paths; the rule files are recognized relative to the workspace
    prefix = str(workspace.resolve()) + os.sep
    relative = [p[len(prefix):] if p.startswith(prefix) else p for p in map(os.path.realpath, st.files_read)]
    guideline_files = sum(bool(GUIDELINE_FILE.match(p)) for p in relative)
    status = (STATUS_TIMEOUT if timed_out
              else STATUS_ERROR if exit_code != 0 or st.error_events else STATUS_OK)
    message = st.error_message
    if not message and status != STATUS_OK:
        stderr_lines = (run_dir / "stderr.log").read_text(encoding="utf-8", errors="replace").splitlines()
        message = stderr_lines[-1] if stderr_lines else ""

    log(f"Run {i}/{args.runs}: {status} | {duration:.0f}s | {usage.tokens_total} tokens | "
        f"{st.tool_calls} tool calls | changes: {changes[1] or '?'}+/{changes[2] or '?'}-")
    return {
        "batch_id": batch.id, "run_index": i, "label": args.label, "prompt": batch.prompt_name,
        "model_requested": args.model, "model_effective": model_effective,
        "start_utc": start_iso, "end_utc": end_iso, "duration_s": f"{duration:.1f}",
        "status": status, "exit_code": exit_code, "error_message": one_line(message, ERROR_MESSAGE_CHARS),
        "steps": usage.steps, "tokens_total": usage.tokens_total, "tokens_input": usage.tokens_input,
        "tokens_output": usage.tokens_output, "tokens_reasoning": usage.tokens_reasoning,
        "tokens_cache_read": usage.tokens_cache_read, "tokens_cache_write": usage.tokens_cache_write,
        "cost_usd": f"{usage.cost_usd:.6f}", "accounting_source": source,
        "tool_calls": st.tool_calls, "tool_errors": st.tool_errors, "mcp_calls": st.mcp_calls,
        "tools_used": ";".join(sorted(st.tools_used)), "output_chars": len(answer),
        "sql_files_read": sum(p.endswith(".sql") for p in st.files_read),
        "guideline_files_read": guideline_files, "knowledge_accessed": int(guideline_files > 0 or st.mcp_calls > 0),
        "files_changed": changes[0], "lines_added": changes[1], "lines_deleted": changes[2],
        "session_id": st.session_id, "prompt_sha256": batch.prompt_sha256,
        "opencode_version": batch.opencode_version, "run_dir": str(run_dir),
    }


def append_row(path: Path, row: dict[str, Any]) -> None:
    """The file is reopened for every row, so completed runs are safe if the script is aborted."""
    new = not path.exists() or path.stat().st_size == 0
    if not new:
        with path.open(newline="", encoding="utf-8") as f:
            if next(csv.reader(f), []) != list(CSV_COLUMNS):
                fail(f"{path} has a different header (older version?). Use another --out directory.")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n")
        if new:
            writer.writeheader()
        writer.writerow(row)


# --------------------------------------------------------------------------- main

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="opencode_multirun.py",
        description="Run one prompt several times with OpenCode, each run in a fresh copy of "
                    "the working directory, and record metrics as CSV.")
    p.add_argument("-f", "--prompt-file", type=Path, required=True, help="file with the prompt")
    p.add_argument("-n", "--runs", type=int, default=1, help="number of runs (default: 1)")
    p.add_argument("-m", "--model", default="", help="model, e.g. github-copilot/claude-sonnet-5")
    p.add_argument("-w", "--workdir", type=Path, default=Path.cwd(),
                   help="directory that is copied for every run (default: current directory)")
    p.add_argument("--add", action="append", default=[], metavar="SRC[:DEST]",
                   help="copy a file or directory into every workspace (repeatable); DEST is relative "
                        "to the workspace, with a trailing '/' it names the target directory")
    p.add_argument("--label", default="", help="name of the experimental condition")
    p.add_argument("-o", "--out", type=Path, default=Path("results"),
                   help="output directory (default: results)")
    args = p.parse_args(argv)
    if args.runs < 1:
        p.error("--runs must be at least 1")
    args.add_specs = [parse_add(s) for s in args.add]
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if os.name != "posix":
        fail("Only POSIX systems are supported (Linux, macOS, WSL2).")
    if not shutil.which("opencode"):
        fail("opencode not found in PATH.")
    if not args.workdir.is_dir():
        fail(f"Working directory does not exist: {args.workdir}")
    try:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        fail(f"Prompt file not readable: {e}")
    if not prompt.strip():
        fail("The prompt is empty.")

    # A fixed prefix + "--" before the prompt keeps a prompt that starts with "-" from being read as an option.
    # --standalone: a private server per run (the shared background service would ignore the
    # isolated environment); --auto: approve permissions that the configuration does not deny.
    cmd = (["opencode", "run", "--standalone", "--auto", "--format", "json"]
           + (["--model", args.model] if args.model else []) + ["--", prompt])
    version = run_quiet(["opencode", "--version"])
    out = args.out.resolve()
    batch_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{os.getpid()}"
    batch = Batch(batch_id, out / batch_id, out / "runs.csv", args.workdir.resolve(), cmd,
                  args.prompt_file.stem, hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                  (version.stdout.strip().splitlines() or [""])[0] if version else "")
    out.mkdir(parents=True, exist_ok=True)
    log(f"Batch {batch_id}: {args.runs} run(s), label '{args.label}', model '{args.model or 'default'}'")
    log(f"Results: {batch.csv_path}  |  raw data: {batch.dir}")

    ok = 0
    try:
        for i in range(1, args.runs + 1):
            row = execute_run(i, args, batch)
            append_row(batch.csv_path, row)
            ok += row["status"] == STATUS_OK
    except KeyboardInterrupt:
        log(f"Aborted by user. The completed runs are in {batch.csv_path}.")
        return 130
    log(f"Done: {ok} of {args.runs} runs ok.")
    return 0  # failed runs are measurement data, not a script error


if __name__ == "__main__":
    sys.exit(main())
