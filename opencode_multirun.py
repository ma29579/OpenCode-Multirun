#!/usr/bin/env python3
"""OpenCode-Multirun: run a prompt repeatedly and non-interactively with OpenCode.

Invokes "opencode run --format json", optionally inside a nono sandbox with
a freely chosen profile ("nono run --profile <PROFILE> -- ..."). For every
run, one row with as many metrics as possible is written to a CSV file.

Collected data (excerpt):
  - Total wall-clock duration, agent duration according to event timestamps,
    time to first event
  - Tokens (total, input, output, reasoning, cache read, cache write)
  - Cost in USD (as reported by OpenCode)
  - Agent steps, tool calls, failed tool calls, tools used, error events,
    length of the text response
  - Exit code, status (ok / error / timeout), session ID, model actually used
  - Git changes in the working directory (files, lines +/-)
  - Prompt hash, OpenCode and nono versions, host, operating system

Background on token and cost accounting:
  With "--format json", OpenCode emits an NDJSON event stream (one JSON
  object per line). Cost and tokens are reported in "step_finish" events,
  PER STEP, so they are summed up. In some OpenCode versions the last
  "step_finish" event is missing from the stream. After every run,
  "opencode export <sessionID>" is therefore evaluated as well; if the export
  data is more complete, it is used instead (column "accounting_source":
  stream / export / none).

Requirements: Python >= 3.9 (standard library only), opencode, optionally
nono and git. Runs on Linux, macOS and WSL2.

Examples:
  ./opencode_multirun.py -p "Explain the class Foo" -n 5
  ./opencode_multirun.py -f prompt.md -n 10 -P nolabs-ai/opencode \\
      -m anthropic/claude-sonnet-4-5 -w ./my-repo --fresh-copy \\
      --label "with-AGENTS.md" -o results.csv
  ./opencode_multirun.py -f prompt.md -n 3 -- --agent build

Note: If the prompt starts with "-", use the equals-sign form:
  ./opencode_multirun.py --prompt="-v is what I mean" -n 2
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import platform
import shlex
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, NoReturn, Optional, Sequence

__version__ = "1.1.0"

# -----------------------------------------------------------------------------
#  Constants
# -----------------------------------------------------------------------------

# CSV columns; do not reorder, so that existing result files stay compatible.
# The names are snake_case on purpose so they can be used in pandas, R or
# Excel without renaming.
CSV_COLUMNS: tuple[str, ...] = (
    "batch_id", "run_index", "runs_total", "label",
    "start_utc", "end_utc", "duration_s", "agent_duration_s", "time_to_first_event_s",
    "exit_code", "status",
    "nono_profile", "model_requested", "model_effective", "agent", "session_id",
    "steps", "tokens_total", "tokens_input", "tokens_output", "tokens_reasoning",
    "tokens_cache_read", "tokens_cache_write", "cost_usd", "finish_reason", "accounting_source",
    "tool_calls", "tool_errors", "tools_used", "error_events", "error_message",
    "output_chars", "event_count", "stderr_lines",
    "git_files_changed", "git_lines_added", "git_lines_deleted", "git_untracked_lines",
    "prompt_sha256", "prompt_chars", "prompt_preview",
    "workdir", "opencode_version", "nono_version", "host", "os", "run_log_dir",
)

# Exit codes of the script.
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
EXIT_INTERRUPTED = 130

# Exit codes of individual runs, as written to the CSV.
EXIT_TIMEOUT = 124       # same as GNU "timeout"
EXIT_NOT_EXECUTABLE = 127  # program could not be started (shell convention)

# Wait between SIGTERM and SIGKILL when terminating a run.
KILL_GRACE_SEC = 10

# Time limits for helper calls (version query, export).
VERSION_TIMEOUT_SEC = 30
EXPORT_TIMEOUT_SEC = 120

# Length limits for CSV text fields.
PROMPT_PREVIEW_CHARS = 80
ERROR_MESSAGE_CHARS = 300

# Values of the CSV column "status".
STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_TIMEOUT = "timeout"

# Values of the CSV column "accounting_source".
SOURCE_STREAM = "stream"
SOURCE_EXPORT = "export"
SOURCE_NONE = "none"

logger = logging.getLogger("opencode_multirun")


# =============================================================================
#  Helper functions
# =============================================================================

def setup_logging() -> None:
    """Status messages with timestamp on stderr (stdout stays free)."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def exit_with_error(msg: str) -> NoReturn:
    """Print an error message and exit the script with code 1."""
    logger.error("ERROR: %s", msg)
    sys.exit(EXIT_CONFIG_ERROR)


def now_iso() -> str:
    """Current time as ISO 8601 in UTC; easy to sort and read."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def one_line(text: str, max_len: Optional[int] = None) -> str:
    """Remove line breaks and tabs (CSV-friendly) and optionally truncate."""
    s = " ".join(text.replace("\t", " ").splitlines())
    if max_len is not None and len(s) > max_len:
        s = s[:max_len] + "…"
    return s


def is_number(value: Any) -> bool:
    """True for int/float, but not for bool (an int subclass in Python)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def num(value: Any) -> float:
    """Convert a JSON value to a number; anything else counts as 0."""
    return value if is_number(value) else 0


def as_dict(value: Any) -> dict:
    """Return value if it is a dict, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def walk_dicts(obj: Any) -> Iterator[dict]:
    """Recursively yield all dictionaries of an arbitrarily nested JSON
    structure. Equivalent to "[.. | objects]" in jq; makes the evaluation
    independent of the exact layout of the export."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_dicts(v)


def tool_version(cmd: Sequence[str]) -> str:
    """First output line of e.g. "opencode --version"; empty on failure."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=VERSION_TIMEOUT_SEC, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return ""
    lines = (res.stdout or res.stderr).strip().splitlines()
    return lines[0].strip() if lines else ""


def fmt(value: Optional[float], digits: int = 3) -> str:
    """Format a float for the CSV; None becomes ""."""
    return "" if value is None else f"{value:.{digits}f}"


# =============================================================================
#  Data structures
# =============================================================================

@dataclass
class Usage:
    """Summed token and cost values of all step-finish parts of a run."""
    steps: int = 0
    tokens_total: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_reasoning: int = 0
    tokens_cache_read: int = 0
    tokens_cache_write: int = 0
    cost_usd: float = 0.0
    finish_reason: str = ""

    @classmethod
    def from_parts(cls, parts: Sequence[dict]) -> Usage:
        """Condense a list of step-finish parts into a Usage.

        If "tokens.total" is missing, it is computed from the individual
        values (OpenCode counts cache tokens in "total").
        """
        u = cls(steps=len(parts))
        for p in parts:
            tok = as_dict(p.get("tokens"))
            cache = as_dict(tok.get("cache"))
            t_in, t_out, t_rea = num(tok.get("input")), num(tok.get("output")), num(tok.get("reasoning"))
            c_read, c_write = num(cache.get("read")), num(cache.get("write"))
            total = tok.get("total")
            if not is_number(total):
                total = t_in + t_out + t_rea + c_read + c_write
            u.tokens_total += int(total)
            u.tokens_input += int(t_in)
            u.tokens_output += int(t_out)
            u.tokens_reasoning += int(t_rea)
            u.tokens_cache_read += int(c_read)
            u.tokens_cache_write += int(c_write)
            u.cost_usd += float(num(p.get("cost")))
            if isinstance(p.get("reason"), str) and p["reason"]:
                u.finish_reason = p["reason"]   # the last reason wins
        return u


@dataclass
class StreamStats:
    """Everything that can be read from the NDJSON event stream of a run."""
    session_id: str = ""
    usage: Usage = field(default_factory=Usage)
    tool_calls: int = 0
    tool_errors: int = 0
    tools_used: set[str] = field(default_factory=set)
    error_events: int = 0
    error_message: str = ""
    output_chars: int = 0
    first_ts: Optional[float] = None    # milliseconds since epoch
    last_ts: Optional[float] = None
    event_count: int = 0


@dataclass(frozen=True)
class BatchContext:
    """Values determined once per invocation and shared by all runs."""
    batch_id: str
    batch_dir: Path
    csv_path: Path
    workdir: Path
    cmd: list[str]
    prompt: str
    prompt_sha256: str
    prompt_preview: str
    host: str
    os_info: str
    opencode_version: str
    nono_version: str
    excludes: frozenset[Path]   # paths to exclude when copying


# =============================================================================
#  Evaluation of event stream and export
# =============================================================================

def extract_error_message(err: Any) -> str:
    """Extract a readable error message from an "error" event.
    The structure varies, so several locations are checked."""
    if isinstance(err, dict):
        data = err.get("data")
        if isinstance(data, dict) and data.get("message"):
            return str(data["message"])
        if err.get("message"):
            return str(err["message"])
        return json.dumps(err, ensure_ascii=False)
    return "" if err is None else str(err)


def parse_events(path: Path) -> StreamStats:
    """Read the NDJSON file produced by "opencode run --format json".

    Lines that are not JSON objects (e.g. nono messages on stdout) are
    skipped silently; this keeps the evaluation robust.
    """
    st = StreamStats()
    step_parts: list[dict] = []
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(ev, dict):
                    _apply_event(st, ev, step_parts)
    except OSError:
        return st

    st.usage = Usage.from_parts(step_parts)
    return st


def _apply_event(st: StreamStats, ev: dict, step_parts: list[dict]) -> None:
    """Apply a single event to the statistics."""
    st.event_count += 1
    if not st.session_id and isinstance(ev.get("sessionID"), str):
        st.session_id = ev["sessionID"]

    # Timestamps (ms) for agent duration and time to first event.
    ts = ev.get("timestamp")
    if is_number(ts):
        st.first_ts = ts if st.first_ts is None else min(st.first_ts, ts)
        st.last_ts = ts if st.last_ts is None else max(st.last_ts, ts)

    part = as_dict(ev.get("part"))
    etype = ev.get("type")

    if etype == "step_finish":
        step_parts.append(part)
    elif etype == "tool_use":
        st.tool_calls += 1
        if isinstance(part.get("tool"), str):
            st.tools_used.add(part["tool"])
        if as_dict(part.get("state")).get("status") == "error":
            st.tool_errors += 1
    elif etype == "error":
        st.error_events += 1
        if not st.error_message:
            st.error_message = extract_error_message(ev.get("error"))
    elif etype == "text":
        st.output_chars += len(str(part.get("text") or ""))


def read_export(session_id: str, cwd: Path, target: Path) -> tuple[Optional[Usage], str]:
    """Read the session via "opencode export" from OpenCode's local database.

    Deliberately runs outside the sandbox, since it only reads its own
    session data. Some versions print a text line before the JSON, so parsing
    starts at the first line beginning with "{".
    Returns: (Usage, or None on failure; model actually used).
    """
    try:
        res = subprocess.run(["opencode", "export", session_id], cwd=cwd,
                             capture_output=True, text=True,
                             timeout=EXPORT_TIMEOUT_SEC, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None, ""

    lines = res.stdout.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("{")), None)
    if start is None:
        return None, ""
    raw = "\n".join(lines[start:])
    try:
        target.write_text(raw, encoding="utf-8")   # raw data for traceability
    except OSError as e:
        logger.warning("Could not save export: %s", e)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, ""

    # Find all step-finish parts, no matter how deeply nested.
    dicts = list(walk_dicts(data))
    usage = Usage.from_parts([d for d in dicts if d.get("type") == "step-finish"])
    # The model used is stored in the message metadata.
    model = next((f"{d['providerID']}/{d['modelID']}" for d in dicts
                  if isinstance(d.get("providerID"), str)
                  and isinstance(d.get("modelID"), str)), "")
    return usage, model


def git_metrics(directory: Path) -> tuple[str, str, str, str]:
    """Git metrics of a directory (read-only, changes nothing):
      1. number of changed/new/deleted files (git status --porcelain)
      2. added lines in tracked files (git diff --numstat HEAD)
      3. deleted lines in tracked files
      4. number of lines in new, untracked files
    No git repo or git not installed -> four empty strings.
    Note: Without --fresh-copy the values are cumulative across all runs.
    """
    empty = ("", "", "", "")
    if not shutil.which("git"):
        return empty

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(directory), *args],
                              capture_output=True, stdin=subprocess.DEVNULL)

    try:
        if git("rev-parse", "--is-inside-work-tree").returncode != 0:
            return empty

        status = git("status", "--porcelain").stdout.decode(errors="replace")
        files = sum(1 for ln in status.splitlines() if ln.strip())

        added = deleted = 0
        numstat = git("diff", "--numstat", "HEAD").stdout.decode(errors="replace")
        for line in numstat.splitlines():
            cols = line.split("\t")
            # Binary files report "-" instead of numbers and are skipped.
            if len(cols) >= 2 and cols[0].isdigit() and cols[1].isdigit():
                added += int(cols[0])
                deleted += int(cols[1])

        untracked_lines = 0
        out = git("ls-files", "--others", "--exclude-standard", "-z").stdout
        for name in filter(None, out.split(b"\0")):
            try:
                untracked_lines += (directory / os.fsdecode(name)).read_bytes().count(b"\n")
            except OSError:
                pass
    except OSError:
        return empty

    return str(files), str(added), str(deleted), str(untracked_lines)


# =============================================================================
#  Process control
# =============================================================================

def terminate_group(proc: subprocess.Popen) -> None:
    """Terminate the started process including all child processes.

    Because the run is started in its own process group, the signal also
    reaches nono and the OpenCode process running inside it.
    First SIGTERM (clean shutdown), then SIGKILL after KILL_GRACE_SEC.
    """
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


def run_process(cmd: Sequence[str], cwd: Path, stdout_path: Path, stderr_path: Path,
                timeout: Optional[int]) -> tuple[int, bool]:
    """Start a run and wait for it to finish.

    - stdin = /dev/null: OpenCode must neither wait for input nor append the
      contents of stdin to the prompt.
    - stdout (events) and stderr (logs, nono messages) go to separate files
      and are not held in memory.
    - start_new_session=True creates a separate process group so that the
      whole process tree can be terminated on timeout or Ctrl+C.

    Returns: (exit code, whether it was terminated due to timeout)
    """
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        try:
            proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL,
                                    stdout=out, stderr=err, start_new_session=True)
        except OSError as e:
            err.write(f"Could not start process: {e}\n".encode())
            return EXIT_NOT_EXECUTABLE, False
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            terminate_group(proc)
            return EXIT_TIMEOUT, True
        except KeyboardInterrupt:
            # Ctrl+C does not reach the separate process group automatically,
            # so terminate it here and pass the interrupt on.
            terminate_group(proc)
            raise
    # Processes killed by a signal report negative codes (e.g. -9).
    # Convert to the shell convention 128 + signal number.
    return (128 - rc if rc < 0 else rc), False


def build_command(args: argparse.Namespace, prompt: str) -> list[str]:
    """Build the invocation as a list, so spaces and special characters in
    prompt or paths are passed safely (no shell involved)."""
    cmd: list[str] = []
    if args.nono_profile:
        # Everything after "--" is started by nono as a child inside the sandbox.
        # The profile can be local (~/.config/nono/profiles/<name>.json)
        # or come from the registry (e.g. "nolabs-ai/opencode").
        cmd += ["nono", "run", "--profile", args.nono_profile, *args.nono_arg, "--"]
    cmd += ["opencode", "run", "--format", "json"]
    if args.model:
        cmd += ["--model", args.model]
    if args.agent:
        cmd += ["--agent", args.agent]
    cmd += args.opencode_args
    # "--" before the prompt so that a prompt with a leading "-" is not
    # mistaken for an option.
    cmd += ["--", prompt]
    return cmd


def copy_workspace(src: Path, dst: Path, excludes: frozenset[Path]) -> None:
    """Copy the working directory for one run (--fresh-copy).

    An existing .git is copied too, so the git metrics only show the changes
    of THIS run. Log directory and CSV are excluded if they live inside the
    working directory; otherwise the agent would see earlier results and the
    logs would copy themselves.
    """
    def ignore(directory: str, names: list[str]) -> list[str]:
        return [n for n in names if (Path(directory) / n).resolve() in excludes]

    shutil.copytree(src, dst, symlinks=True, ignore=ignore)


# =============================================================================
#  CSV
# =============================================================================

def prepare_csv(path: Path, delimiter: str) -> None:
    """Write the header row if the file is new or empty.
    Warn if an existing file has a different header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        with path.open(newline="", encoding="utf-8") as f:
            header = next(csv.reader(f, delimiter=delimiter), [])
        if header != list(CSV_COLUMNS):
            logger.warning("WARNING: Header in %s differs (different delimiter "
                           "or older version?). Rows are appended anyway.", path)
        return
    append_csv_row(path, delimiter, CSV_COLUMNS)


def append_csv_row(path: Path, delimiter: str, values: Sequence[Any]) -> None:
    """Append one row. The file is reopened for every row so that all runs
    completed so far are safe if the script is aborted.
    QUOTE_ALL and "\\n" as line ending are part of the existing file format."""
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=delimiter, quoting=csv.QUOTE_ALL,
                   lineterminator="\n").writerow(values)


# =============================================================================
#  Command line
# =============================================================================

def positive_int(text: str) -> int:
    """argparse type: integer >= 1."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an integer: {text!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def non_negative_float(text: str) -> float:
    """argparse type: float >= 0."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from None
    if value < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Define all command-line parameters."""
    p = argparse.ArgumentParser(
        prog="opencode_multirun.py",
        description="Run a prompt repeatedly with OpenCode (optionally in a "
                    "nono sandbox) and log metrics as CSV.",
        epilog="Everything after '--' is passed to 'opencode run'.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("-p", "--prompt", help="Prompt as text")
    src.add_argument("-f", "--prompt-file", type=Path, help="Prompt from file")

    p.add_argument("-n", "--runs", type=positive_int, default=1,
                   help="Number of runs (default: 1)")
    p.add_argument("-P", "--nono-profile", default="",
                   help="nono profile; without it OpenCode runs without a sandbox")
    p.add_argument("--nono-arg", action="append", default=[],
                   help="Additional argument for 'nono run' (repeatable)")
    p.add_argument("-m", "--model", default="",
                   help="Model, e.g. anthropic/claude-sonnet-4-5")
    p.add_argument("-a", "--agent", default="",
                   help="OpenCode agent, e.g. build or plan")
    p.add_argument("-o", "--output", type=Path, default=Path("opencode-runs.csv"),
                   help="CSV file (default: ./opencode-runs.csv)")
    p.add_argument("-l", "--log-dir", type=Path, default=Path("opencode-runs"),
                   help="Raw data per run (default: ./opencode-runs)")
    p.add_argument("-w", "--workdir", type=Path, default=Path.cwd(),
                   help="Working directory of the agent (default: current)")
    p.add_argument("--fresh-copy", action="store_true",
                   help="Every run works on a fresh copy of --workdir")
    p.add_argument("-t", "--timeout", type=positive_int, default=None,
                   help="Time limit per run in seconds")
    p.add_argument("-s", "--sleep", type=non_negative_float, default=0.0,
                   help="Pause between runs in seconds")
    p.add_argument("--label", default="",
                   help="Free-text label for the experimental condition")
    p.add_argument("-d", "--delimiter", default=",",
                   help="CSV delimiter (default: ','; use ';' for German Excel)")
    p.add_argument("--no-export", action="store_true",
                   help="Skip the cross-check via 'opencode export'")
    p.add_argument("--dry-run", action="store_true",
                   help="Only show the commands, run nothing")
    return p


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Read the parameters. Everything after the first "--" is passed through
    to "opencode run" unchanged and is therefore split off beforehand."""
    argv = list(sys.argv[1:] if argv is None else argv)
    passthrough: list[str] = []
    if "--" in argv:
        idx = argv.index("--")
        argv, passthrough = argv[:idx], argv[idx + 1:]

    parser = build_parser()
    args = parser.parse_args(argv)
    args.opencode_args = passthrough
    if len(args.delimiter) != 1:
        parser.error("--delimiter must be exactly one character")
    return args


# =============================================================================
#  Summary
# =============================================================================

def print_summary(rows: Sequence[dict]) -> None:
    """Print metrics over all runs of this invocation to stderr:
    sum, mean, median and, from two runs on, standard deviation.
    The spread in particular is revealing for repeated agent runs."""
    if not rows:
        return
    ok = sum(1 for r in rows if r["status"] == STATUS_OK)
    print(f"\nSummary: {len(rows)} runs, {ok} ok", file=sys.stderr)

    def describe(label: str, key: str, unit: str, digits: int) -> None:
        vals = [float(r[key]) for r in rows if r[key] not in ("", None)]
        if not vals:
            return
        sd = f"  sd {statistics.stdev(vals):.{digits}f}" if len(vals) > 1 else ""
        print(f"  {label:<10} sum {sum(vals):.{digits}f}{unit}  "
              f"mean {statistics.mean(vals):.{digits}f}  "
              f"median {statistics.median(vals):.{digits}f}{sd}", file=sys.stderr)

    describe("Cost", "cost_usd", " USD", 4)
    describe("Duration", "duration_s", " s", 1)
    describe("Tokens", "tokens_total", "", 0)
    describe("Tool calls", "tool_calls", "", 1)


# =============================================================================
#  Orchestration
# =============================================================================

def load_prompt(args: argparse.Namespace) -> str:
    """Read the prompt from file or argument and ensure it is not empty."""
    if args.prompt_file is not None:
        try:
            prompt = args.prompt_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            exit_with_error(f"Prompt file not readable: {e}")
    else:
        prompt = args.prompt
    if not prompt.strip():
        exit_with_error("The prompt is empty.")
    return prompt


def check_prerequisites(args: argparse.Namespace) -> None:
    """Check platform, required programs and the working directory."""
    if os.name != "posix":
        exit_with_error("Only POSIX systems are supported (Linux, macOS, WSL2).")
    if not args.dry_run:
        if not shutil.which("opencode"):
            exit_with_error("opencode not found in PATH.")
        if args.nono_profile and not shutil.which("nono"):
            exit_with_error("nono not found in PATH, but a profile was given.")
    if not args.workdir.is_dir():
        exit_with_error(f"Working directory does not exist: {args.workdir}")


def build_context(args: argparse.Namespace, prompt: str) -> BatchContext:
    """Determine all values that apply to every run of this invocation."""
    log_dir = args.log_dir.resolve()
    csv_path = args.output.resolve()
    # Unique ID of this invocation so runs can be grouped later, even when
    # several invocations write to the same CSV.
    batch_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{os.getpid()}"
    versions_needed = not args.dry_run
    return BatchContext(
        batch_id=batch_id,
        batch_dir=log_dir / batch_id,
        csv_path=csv_path,
        workdir=args.workdir.resolve(),
        cmd=build_command(args, prompt),
        prompt=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        prompt_preview=one_line(prompt, PROMPT_PREVIEW_CHARS),
        host=socket.gethostname(),
        os_info=f"{platform.system()} {platform.release()}",
        opencode_version=tool_version(["opencode", "--version"]) if versions_needed else "",
        nono_version=(tool_version(["nono", "--version"])
                      if versions_needed and args.nono_profile else ""),
        excludes=frozenset({log_dir, csv_path}),
    )


def dry_run(args: argparse.Namespace, ctx: BatchContext) -> None:
    """Show working directory and command per run without executing anything."""
    for i in range(1, args.runs + 1):
        cwd = ctx.batch_dir / f"run-{i:03d}" / "workspace" if args.fresh_copy else ctx.workdir
        logger.info("Run %d/%d (dry run) in %s:", i, args.runs, cwd)
        print("  " + shlex.join(ctx.cmd), file=sys.stderr)


def derive_timings(st: StreamStats, start_epoch: float) -> tuple[Optional[float], Optional[float]]:
    """Agent duration (first to last event timestamp) and time to first event.
    The latter includes the startup of nono/OpenCode (sandbox setup,
    configuration, first model call)."""
    if st.first_ts is None or st.last_ts is None:
        return None, None
    agent_duration = (st.last_ts - st.first_ts) / 1000
    # Plausibility check: only real epoch milliseconds (> 2001) are comparable
    # with the start time.
    ttfe = st.first_ts / 1000 - start_epoch if st.first_ts > 1e12 else None
    return agent_duration, ttfe


def classify_status(exit_code: int, timed_out: bool, error_events: int) -> str:
    """Derive the status of a run from exit code and error events."""
    if timed_out:
        return STATUS_TIMEOUT
    if exit_code != 0 or error_events > 0:
        return STATUS_ERROR
    return STATUS_OK


def execute_run(i: int, args: argparse.Namespace, ctx: BatchContext) -> dict[str, Any]:
    """Execute one run and return the CSV row as a dictionary.

    Raises KeyboardInterrupt if the user aborts during the run.
    """
    run_dir = ctx.batch_dir / f"run-{i:03d}"
    events_file = run_dir / "events.jsonl"   # stdout of opencode (NDJSON)
    stderr_file = run_dir / "stderr.log"     # stderr of opencode/nono
    export_file = run_dir / "export.json"    # result of "opencode export"
    run_dir.mkdir(parents=True, exist_ok=True)

    # ---- Working directory for this run -------------------------------------
    if args.fresh_copy:
        run_workdir = run_dir / "workspace"
        try:
            copy_workspace(ctx.workdir, run_workdir, ctx.excludes)
        except (OSError, shutil.Error) as e:
            exit_with_error(f"Copying the working directory failed: {e}")
    else:
        run_workdir = ctx.workdir

    # Store the exact command for traceability.
    (run_dir / "command.txt").write_text(shlex.join(ctx.cmd) + "\n", encoding="utf-8")
    logger.info("Run %d/%d started …", i, args.runs)

    # ---- Execution with timing ----------------------------------------------
    # time.time() for the absolute start time (to compare with the event
    # timestamps), perf_counter() for the precise duration.
    start_iso, start_epoch, t0 = now_iso(), time.time(), time.perf_counter()
    exit_code, timed_out = run_process(ctx.cmd, run_workdir, events_file,
                                       stderr_file, args.timeout)
    duration = time.perf_counter() - t0
    end_iso = now_iso()

    # ---- Evaluate the event stream ------------------------------------------
    st = parse_events(events_file)
    usage = st.usage
    accounting_source = SOURCE_STREAM
    model_effective = ""

    # Cross-check via "opencode export": export values are adopted if they
    # contain at least as many steps as the stream.
    if not args.no_export and st.session_id:
        x_usage, model_effective = read_export(st.session_id, run_workdir, export_file)
        if x_usage is not None and x_usage.steps > 0 and x_usage.steps >= usage.steps:
            usage = x_usage
            accounting_source = SOURCE_EXPORT
    if usage.steps == 0:
        accounting_source = SOURCE_NONE   # no accounting data found at all

    agent_duration, ttfe = derive_timings(st, start_epoch)

    try:
        stderr_lines = stderr_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        stderr_lines = []

    status = classify_status(exit_code, timed_out, st.error_events)

    # Error message: preferably from the event stream, else the last stderr line.
    error_message = st.error_message
    if not error_message and status != STATUS_OK and stderr_lines:
        error_message = stderr_lines[-1]
    error_message = one_line(error_message, ERROR_MESSAGE_CHARS)

    git_files, git_add, git_del, git_untracked = git_metrics(run_workdir)

    logger.info("Run %d/%d: %s | %.1fs | %d tokens | $%.4f | source: %s",
                i, args.runs, status, duration, usage.tokens_total,
                usage.cost_usd, accounting_source)

    # A dictionary makes the mapping to columns explicit; the order in the
    # file is determined solely by CSV_COLUMNS.
    return {
        "batch_id": ctx.batch_id, "run_index": i, "runs_total": args.runs,
        "label": args.label,
        "start_utc": start_iso, "end_utc": end_iso,
        "duration_s": fmt(duration), "agent_duration_s": fmt(agent_duration),
        "time_to_first_event_s": fmt(ttfe),
        "exit_code": exit_code, "status": status,
        "nono_profile": args.nono_profile, "model_requested": args.model,
        "model_effective": model_effective, "agent": args.agent,
        "session_id": st.session_id,
        "steps": usage.steps, "tokens_total": usage.tokens_total,
        "tokens_input": usage.tokens_input, "tokens_output": usage.tokens_output,
        "tokens_reasoning": usage.tokens_reasoning,
        "tokens_cache_read": usage.tokens_cache_read,
        "tokens_cache_write": usage.tokens_cache_write,
        "cost_usd": fmt(usage.cost_usd, 6), "finish_reason": usage.finish_reason,
        "accounting_source": accounting_source,
        "tool_calls": st.tool_calls, "tool_errors": st.tool_errors,
        "tools_used": ";".join(sorted(st.tools_used)),
        "error_events": st.error_events, "error_message": error_message,
        "output_chars": st.output_chars, "event_count": st.event_count,
        "stderr_lines": len(stderr_lines),
        "git_files_changed": git_files, "git_lines_added": git_add,
        "git_lines_deleted": git_del, "git_untracked_lines": git_untracked,
        "prompt_sha256": ctx.prompt_sha256, "prompt_chars": len(ctx.prompt),
        "prompt_preview": ctx.prompt_preview,
        "workdir": str(run_workdir), "opencode_version": ctx.opencode_version,
        "nono_version": ctx.nono_version, "host": ctx.host, "os": ctx.os_info,
        "run_log_dir": str(run_dir),
    }


# =============================================================================
#  Main program
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    setup_logging()
    args = parse_args(argv)
    prompt = load_prompt(args)
    check_prerequisites(args)
    ctx = build_context(args, prompt)

    if args.dry_run:
        dry_run(args, ctx)
        return EXIT_OK

    prepare_csv(ctx.csv_path, args.delimiter)
    logger.info("Batch %s: %d run(s), profile: %s, model: %s",
                ctx.batch_id, args.runs, args.nono_profile or "<no sandbox>",
                args.model or "<default>")
    logger.info("CSV: %s  |  raw data: %s", ctx.csv_path, ctx.batch_dir)

    results: list[dict[str, Any]] = []
    interrupted = False

    for i in range(1, args.runs + 1):
        try:
            row = execute_run(i, args, ctx)
        except KeyboardInterrupt:
            logger.info("Aborted by user – the current run is not logged.")
            interrupted = True
            break
        append_csv_row(ctx.csv_path, args.delimiter, [row[c] for c in CSV_COLUMNS])
        results.append(row)

        # Optional pause before the next run (not after the last one).
        if i < args.runs and args.sleep > 0:
            try:
                time.sleep(args.sleep)
            except KeyboardInterrupt:
                interrupted = True
                break

    print_summary(results)
    if interrupted:
        logger.info("Results so far are in %s", ctx.csv_path)
        return EXIT_INTERRUPTED
    # Failed runs are measurement data, not a script error -> exit code 0.
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
