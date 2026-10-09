# AGENTS.md

Guidance for AI coding agents (OpenCode, Claude Code, etc.) working in this repository.

## Project overview

OpenCode-Multirun (`opencode_multirun.py`) runs a prompt repeatedly and non-interactively with OpenCode (`opencode run --format json`), optionally inside a nono sandbox, and writes one row of metrics per run (tokens, cost, duration, tool usage, git changes) to a CSV file. It is developed as part of a master's thesis; results must be **reproducible and comparable**.

Files:

| File | Purpose |
|---|---|
| `opencode_multirun.py` | The entire program (single file, standard library only) |
| `README.md` | User documentation (parameters, CSV columns, examples) |
| `AGENTS.md` | This file |

## Environment and commands

- Python ≥ 3.9, **no dependencies beyond the standard library**. Do not add new packages.
- Supported: Linux, macOS, WSL2 (POSIX). Native Windows is excluded (process groups via `os.killpg`).
- Syntax check: `python3 -m py_compile opencode_multirun.py`
- Preview commands without running: `./opencode_multirun.py -p "test" -n 2 -P nolabs-ai/opencode --dry-run`
- There is no automated test suite. To test without real API costs, put a fake `opencode` (a shell script printing NDJSON lines) first in `PATH` and write to a temporary directory (`-o`, `-l`).

## Architecture (`opencode_multirun.py`)

Flow in `main()`: `parse_args` → `load_prompt` → `check_prerequisites` → `build_context` → per run `execute_run` → `append_csv_row` → `print_summary`.

- `Usage`, `StreamStats`, `BatchContext`: dataclasses for measurements and invocation context.
- `parse_events` / `_apply_event`: evaluates the NDJSON stream; skips non-JSON lines.
- `read_export`: cross-check via `opencode export <sessionID>`, because the last `step_finish` may be missing from the stream.
- `run_process` / `terminate_group`: start in a separate process group; SIGTERM on timeout, then SIGKILL.
- `build_command`: assembles `<sandbox-cmd> --profile P [nono-args] -- <opencode-cmd> run --format json … -- <prompt>`. Sandbox and OpenCode commands are configurable (`--sandbox-cmd`, `--opencode-cmd`, `--sandbox-is-opencode` for launchers that are OpenCode itself) because the nono CLI differs between versions; never hard-code `nono`, `run` or `opencode` elsewhere.
- `git_metrics`: read-only git calls.

## Must be observed

1. **The CSV format is a contract.** Columns and their order in `CSV_COLUMNS` must not change. Existing result files continue to be appended to and must stay compatible. New columns only with explicit approval; append them at the end and update the README.
2. **Status and source values stay unchanged:** `status` ∈ `ok`/`error`/`timeout`, `accounting_source` ∈ `stream`/`export`/`none`, exit code `124` for timeout. Analyses in R/pandas depend on these.
3. **Failed runs are measurement data.** The script still exits with code 0. Exit codes: `0` ok, `1` configuration error, `2` invalid parameters (argparse), `130` Ctrl+C.
4. **No shell strings.** Always pass commands to `subprocess` as a list; the prompt follows `--` so that a leading `-` is not treated as an option.
5. **Robustness over strictness:** The evaluation must cope with missing fields and unknown event types (`as_dict`, `num`). Raw data (`events.jsonl`, `export.json`, `stderr.log`) is always kept.
6. **Write completed runs to the CSV immediately**, so an abort does not lose data.
7. **Do not weaken `--fresh-copy`:** the log directory and CSV are excluded when copying so the agent never sees earlier results.

## Code style

- Comments, docstrings, log and error messages in **English**; identifiers and CSV column names in snake_case.
- Type annotations throughout; keep `from __future__ import annotations` (Python 3.9).
- Magic numbers as named constants at the top of the file.
- Status output via `logger`; summary and dry-run commands go to stderr; stdout stays free.
- Comments explain *why*, not *what*. Do not remove documented decisions (e.g. `perf_counter` vs. `time`) without reason.
- Keep changes small; no restructuring without a request.

## Keeping documentation current

If a parameter, CSV column, exit code or behavior changes, update `README.md` and the module docstring in the same change. Bump `__version__` on behavior changes.

## Caution

- Real runs incur API costs and modify the working directory. Without `--fresh-copy` the agent works directly in the given `--workdir`. Use `--dry-run` or a fake `opencode` to verify.
- Do not commit or echo API keys, session exports or result CSVs containing prompts.
