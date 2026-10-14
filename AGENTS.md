# AGENTS.md

Guidance for AI coding agents (OpenCode, Claude Code, etc.) that work **on this repository**. The repository itself is the setup of a pilot study in which other agents are measured; keep that in mind before every change.

## Project overview

A pilot study for a master's thesis: how does an agent handle a prompt and the knowledge that is provided to it? The tool `tools/opencode_multirun.py` runs a prompt several times with OpenCode and records quantitative metrics; `tools/schema_lint.py` checks the schema the agent produced against the rules. The agent under test works on `sample_project/` (a PostgreSQL schema with deliberate violations) and gets the guidelines from `sample_guidelines/` in six scenarios (baseline, AGENTS.md, files, specs, MCP, hybrid). See `README.md` for the study design.

| Path | Purpose |
|---|---|
| `tools/opencode_multirun.py` | the measuring tool (single file, standard library only) |
| `tools/schema_lint.py` | the linter (standard library, needs Docker for a throw-away PostgreSQL) |
| `study/` | prompts, configuration, scenario builder and runners, ground truth |
| `study/scenarios/` | **generated** by `study/build-scenarios.py` from `sample_guidelines/`; never edit by hand |
| `sample_project/` | object of the study: `db/migrations/*.sql`, `db/scripts/*.sql` |
| `sample_guidelines/` | the knowledge given to the agent under test |
| `docker-compose.yml`, `.env.example` | the two docs MCP servers (Ollama and OpenCode run on the host) |
| `study/setup-ollama.sh` | pulls the embedding model into the local Ollama |

## Keep the study valid

1. **Never leak the ground truth.** `study/ground-truth/` must not be copied into `sample_project/`, `sample_guidelines/`, `study/prompts/` or `study/config/`, and no file the agent under test can see may mention the built-in violations. Do not add comments such as "bad", "wrong" or "violates" to the sample SQL.
2. **Keep the relation of the guidelines hidden.** Names, titles and rule IDs of the three guideline files are neutral on purpose. Do not add descriptions that say that one guideline extends or contradicts another. The relation belongs only into the ground truth.
3. **Keep prompts identical across scenarios.** A prompt must not name a specific guideline, spec or file; the scenarios differ only in the provided knowledge, and all of them carry the same 32 rules.
4. **Changing the sample changes the ground truth and the linter.** If you change a migration or a guideline, update `study/ground-truth/violations.md` in the same change, update the matching check in `tools/schema_lint.py` (it stops if the rule IDs differ from the guidelines), assign a new rule to a capability in `study/build-scenarios.py`, rebuild the scenarios (`study/build-scenarios.py`) and verify the migrations (see below). Compare the linter on the unchanged `sample_project/` with the ground truth.
5. **Do not delete data of finished runs.** `results/` is ignored by git; never overwrite a result file. A new study uses a new `--out` directory.

## The tool (`tools/opencode_multirun.py`)

- Python ≥ 3.9, **standard library only**, POSIX only (process groups via `os.killpg`).
- Flow: `parse_args` → `main` → per run `execute_run` (copy workspace, add files, git baseline, run `opencode run --format json`, evaluate stream and export, collect changes, append CSV row).
- Every run works in its own copy of the working directory. The original must never be changed.
- OpenCode 2.x is required: `opencode run --standalone --auto --format json`, `opencode session export --standalone`. `--standalone` gives every run a private server; the shared background service of OpenCode would ignore the isolated environment.
- **Start OpenCode only through `env_for`.** OpenCode takes its project directory from the `PWD` variable, not from the real working directory. Without `PWD` the agent would work in the directory the tool was started from (the repository itself). `env_for` also points `XDG_CONFIG_HOME` to an empty directory so that the personal OpenCode configuration of the user cannot leak into a run, and removes `OPENCODE_*` variables.
- Failed runs are measurement data: the tool exits with `0`. Exit codes: `0` ok, `1` configuration error, `2` invalid parameters, `130` Ctrl+C.
- `CSV_COLUMNS` is the contract of the result files. Changing it requires a new `__version__` and a note in `README.md`.
- Pass commands to `subprocess` as lists, never as shell strings. The prompt follows `--`.
- The evaluation must cope with missing fields and unknown event types (`as_dict`, `num`). Raw data (`events.jsonl`, `response.txt`, `changes.patch`) is always kept.
- Keep the tool small. Do not add options that the study does not use.
- Comments, docstrings and messages in English; identifiers in snake_case; type annotations; keep `from __future__ import annotations`.

## Commands

```bash
python3 -m py_compile tools/opencode_multirun.py tools/schema_lint.py study/build-scenarios.py   # syntax check
python3 study/build-scenarios.py                      # rebuild study/scenarios/ after a change of the guidelines
docker compose config -q                              # validate the compose file
bash -n study/run.sh study/run-all.sh study/index-knowledge.sh   # validate the shell scripts
```

There is no automated test suite. To test the tool without real model calls, put a fake `opencode` (a shell script that prints NDJSON events and changes files in its working directory) first in `PATH` and write to a temporary `--out` directory.

To test the linter, create a results directory with a `runs.csv` (columns `batch_id`, `run_index`, `label`, `prompt`, `status`, `run_dir`) whose run directories contain a `workspace/` copy of `sample_project/` with an additional `V8` migration, and run `tools/schema_lint.py` on it.

To verify the SQL, apply `sample_project/db/migrations/V*.sql` in order to a throw-away PostgreSQL database, e.g. `docker run --rm -d -e POSTGRES_PASSWORD=x postgres:17-alpine`, and stop the container afterwards.

## Caution

- Real runs cost time and, with cloud models, money. Use a fake `opencode` for verification.
- Do not commit API keys, `.env` files or result files that contain prompts.
