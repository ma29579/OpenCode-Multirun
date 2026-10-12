# OpenCode-Multirun

OpenCode-Multirun (`opencode_multirun.py`) runs a prompt repeatedly and non-interactively with [OpenCode](https://opencode.ai), optionally inside a [nono](https://github.com/nolabs-ai/nono) sandbox with a freely chosen profile, and logs cost, tokens, duration, tool usage, errors and git changes for every run to a CSV file.

The script is meant for **repeated, comparable agent runs**, for example to benchmark different prompts, models, agent configurations or sandbox profiles against each other and to analyze the variance between repetitions.

---

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Parameters](#parameters)
- [Examples](#examples)
- [Output](#output)
- [CSV columns](#csv-columns)
- [How tokens and cost are collected](#how-tokens-and-cost-are-collected)
- [Analysis with pandas](#analysis-with-pandas)
- [Notes and limitations](#notes-and-limitations)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Requirements

| Component | Required | Purpose |
|---|---|---|
| Python ≥ 3.9 | yes | Runs the script (standard library only) |
| `opencode` in `PATH` | yes | The actual agent |
| `nono` in `PATH` | only with `-P` | Sandbox for the agent |
| `git` | optional | Metrics on file changes |

Supported systems: **Linux, macOS and Windows via WSL2**. Native Windows is not supported because process groups are terminated via POSIX signals.

## Installation

```bash
chmod +x opencode_multirun.py
# optionally make it available globally
ln -s "$PWD/opencode_multirun.py" ~/.local/bin/opencode-multirun
```

No Python packages need to be installed.

## Quick start

```bash
# Three runs without sandbox, results in ./opencode-runs.csv
./opencode_multirun.py -p "Summarize the architecture of this repo" -n 3

# Ten runs in the nono sandbox, each on a fresh copy of the repo
./opencode_multirun.py -f prompt.md -n 10 \
  -P nolabs-ai/opencode \
  -m anthropic/claude-sonnet-4-5 \
  -w ./my-repo --fresh-copy \
  --label "baseline"
```

Before the first real run it is worth checking the generated command:

```bash
./opencode_multirun.py -f prompt.md -n 2 -P nolabs-ai/opencode --dry-run
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `-p`, `--prompt TEXT` | – | Prompt as text. Either `-p` or `-f` is required. |
| `-f`, `--prompt-file FILE` | – | Read the prompt from a file (UTF-8). |
| `-n`, `--runs N` | `1` | Number of runs. |
| `-P`, `--nono-profile NAME` | – | nono profile. Without it, OpenCode runs without a sandbox. Local profiles (`~/.config/nono/profiles/<name>.json`) and registry profiles (e.g. `nolabs-ai/opencode`) are possible. |
| `--nono-arg ARG` | – | Additional argument for `nono run`. Repeatable. |
| `-m`, `--model PROV/MODEL` | OpenCode default | Model in the format `provider/model`. |
| `-a`, `--agent NAME` | OpenCode default | OpenCode agent, e.g. `build` or `plan`. |
| `-o`, `--output FILE` | `./opencode-runs.csv` | Target CSV. If it exists, rows are appended. |
| `-l`, `--log-dir DIR` | `./opencode-runs` | Location of the raw data per run. |
| `-w`, `--workdir DIR` | current directory | Working directory of the agent. |
| `--fresh-copy` | off | Every run works on its own copy of `--workdir` (including `.git`). |
| `-t`, `--timeout SEC` | no limit | Time limit per run. Then SIGTERM, after 10 s SIGKILL. |
| `-s`, `--sleep SEC` | `0` | Pause between runs, e.g. because of rate limits. |
| `--label TEXT` | – | Free text to label the experimental condition. |
| `-d`, `--delimiter C` | `,` | CSV delimiter. Use `;` for German Excel. |
| `--no-export` | off | Skip the cross-check via `opencode export` (see below). |
| `--dry-run` | off | Only show the commands; run and write nothing. |
| `--version` | – | Print the script version. |
| `-- ARGS…` | – | Everything after `--` is passed to `opencode run` unchanged. |

**Prompt starts with `-`?** Use the equals-sign form, otherwise argparse mistakes it for an option:

```bash
./opencode_multirun.py --prompt="-v should enable verbose logs. Implement that." -n 2
```

## Examples

**Compare experimental conditions** – several invocations write to the same CSV and are distinguished by `--label`:

```bash
for cond in no-context with-agents-md; do
  ./opencode_multirun.py -f "prompts/$cond.md" -n 10 \
    -w ./repo --fresh-copy -P nolabs-ai/opencode \
    --label "$cond" -o comparison.csv -s 5
done
```

**Compare several models:**

```bash
for model in anthropic/claude-sonnet-4-5 openai/gpt-5; do
  ./opencode_multirun.py -f prompt.md -n 5 -m "$model" --fresh-copy -o models.csv
done
```

**Custom nono profile based on the official one:**

```bash
nono profile init my-opencode --extends nolabs-ai/opencode
# adjust the profile, then:
./opencode_multirun.py -f prompt.md -n 5 -P my-opencode
```

**Pass additional OpenCode options through:**

```bash
./opencode_multirun.py -f prompt.md -n 3 -- --agent plan
```

## Output

### Directory structure

Every invocation forms a **batch** with a unique ID (`<UTC timestamp>-<PID>`):

```
opencode-runs/
└── 20261002T155622Z-4711/
    ├── run-001/
    │   ├── command.txt     # exact command that was executed
    │   ├── events.jsonl    # NDJSON event stream from OpenCode (stdout)
    │   ├── stderr.log      # logs from OpenCode and nono
    │   ├── export.json     # result of "opencode export" (if available)
    │   └── workspace/      # only with --fresh-copy: working copy after the run
    └── run-002/
        └── …
```

The working copies are kept. This allows checking afterwards what the agent actually changed, e.g. with `git -C run-001/workspace diff`.

### Console

Status messages appear on stderr while the runs are in progress. At the end a summary follows with sum, mean, median and standard deviation (sd, from two runs on):

```
Summary: 10 runs, 9 ok
  Cost       sum 1.8421 USD  mean 0.1842  median 0.1790  sd 0.0312
  Duration   sum 812.4 s  mean 81.2  median 78.9  sd 12.7
  Tokens     sum 1843210  mean 184321  median 179044  sd 30112
  Tool calls sum 214.0  mean 21.4  median 20.0  sd 4.1
```

### Exit codes of the script

| Code | Meaning |
|---|---|
| `0` | All runs were executed. Failed runs count as measurement data, not as a script error. |
| `1` | Configuration error (e.g. `opencode` not found, prompt file missing). |
| `2` | Invalid parameters. |
| `130` | Aborted with Ctrl+C. All runs completed up to that point are already in the CSV. |

## CSV columns

All fields are quoted; the decimal separator is always a period. The header row is only written if the file is new or empty.

### Run and time

| Column | Description |
|---|---|
| `batch_id` | ID of the invocation; groups related runs. |
| `run_index`, `runs_total` | Number of the run and total number in the batch. |
| `label` | Value of `--label`. |
| `start_utc`, `end_utc` | Start and end in UTC (ISO 8601). |
| `duration_s` | Total wall-clock duration including startup of nono and OpenCode. |
| `agent_duration_s` | Time between first and last event according to OpenCode timestamps. |
| `time_to_first_event_s` | Time until the first event: sandbox setup, configuration and first model response. |
| `exit_code` | Exit code of the process. `124` = timeout, `127` = process could not be started, `128+N` = terminated by signal N. |
| `status` | `ok`, `error` (exit code ≠ 0 or error event) or `timeout`. |

### Configuration

| Column | Description |
|---|---|
| `nono_profile` | nono profile used; empty without sandbox. |
| `model_requested` | Value of `--model`. |
| `model_effective` | Model actually used according to the session export. |
| `agent` | Value of `--agent`. |
| `session_id` | OpenCode session ID, e.g. for `opencode export`. |

### Tokens and cost

| Column | Description |
|---|---|
| `steps` | Number of agent steps (`step_finish` events). |
| `tokens_total` | Sum of all tokens **including** cache. |
| `tokens_input`, `tokens_output`, `tokens_reasoning` | Uncached input, output and reasoning tokens. |
| `tokens_cache_read`, `tokens_cache_write` | Tokens read from or written to the prompt cache. |
| `cost_usd` | Cost in USD as calculated by OpenCode (6 decimal places). |
| `finish_reason` | Reason the last step ended, e.g. `stop` or `tool-calls`. |
| `accounting_source` | Origin of token and cost values: `export`, `stream` or `none`. |

### Agent behavior

| Column | Description |
|---|---|
| `tool_calls` | Number of tool calls. |
| `tool_errors` | Of these, how many failed. |
| `tools_used` | Tools used, alphabetical and `;`-separated. |
| `error_events` | Number of error events in the stream. |
| `error_message` | First error message (max. 300 characters), otherwise the last stderr line. |
| `output_chars` | Length of the text response in characters. |
| `event_count` | Number of valid JSON events. |
| `stderr_lines` | Number of lines on stderr. |

### Changes in the working directory

These columns stay empty if the directory is not a git repository.

| Column | Description |
|---|---|
| `git_files_changed` | Changed, new or deleted files according to `git status --porcelain`. |
| `git_lines_added`, `git_lines_deleted` | Line changes in tracked files compared to `HEAD`. |
| `git_untracked_lines` | Lines in new, untracked files. |

### Prompt and environment

| Column | Description |
|---|---|
| `prompt_sha256` | Hash of the prompt. Identical prompts can be matched reliably. |
| `prompt_chars` | Length of the prompt in characters. |
| `prompt_preview` | The first 80 characters, on one line. |
| `workdir` | Working directory of the run. |
| `opencode_version`, `nono_version` | Tool versions. |
| `host`, `os` | Host name and operating system. |
| `run_log_dir` | Path to the raw data of this run. |

## How tokens and cost are collected

With `--format json`, OpenCode writes an NDJSON event stream, i.e. one JSON object per line. Tokens and cost appear in the `step_finish` events **per step**; the script sums them over all steps.

In some OpenCode versions the process can end before the last `step_finish` event is emitted. The session data is nevertheless stored completely. After every run the script therefore also reads `opencode export <sessionID>` and adopts those values if they contain at least as many steps as the stream. The column `accounting_source` shows the result:

- `export` – values from the session export (preferred, complete)
- `stream` – values from the event stream (export unavailable or disabled)
- `none` – no accounting data found, e.g. after an immediate abort

The export runs outside the sandbox since it only reads OpenCode's local session data. It can be disabled with `--no-export`.

**Note on `cost_usd`:** The value is OpenCode's own calculation based on model prices. For subscriptions, local models (e.g. via Ollama) or providers without pricing it can be `0` although tokens were consumed.

## Analysis with pandas

```python
import pandas as pd

df = pd.read_csv("comparison.csv")          # with -d ';' also pass sep=";"

# Only successful runs with complete accounting data
ok = df[(df.status == "ok") & (df.accounting_source != "none")]

# Metrics per experimental condition
print(
    ok.groupby("label")[["cost_usd", "duration_s", "tokens_total", "tool_calls"]]
      .agg(["mean", "median", "std", "count"])
      .round(3)
)

# Success rate per condition
print(df.groupby("label").status.value_counts(normalize=True).unstack())
```

## Notes and limitations

- **Independent repetitions:** Without `--fresh-copy` all runs work in the same directory. Changes from earlier runs then influence later ones, and the git metrics are cumulative. For comparable measurements, `--fresh-copy` should be set.
- **Log directory inside the working directory:** If the log directory or CSV lies inside `--workdir`, they are excluded when copying. This way the agent never sees earlier results.
- **Permission prompts:** Depending on the OpenCode version and configuration, a non-interactive run can get stuck on permission prompts. Suitable `permission` settings in the OpenCode configuration or version-dependent flags after `--` help. The nono sandbox limits what the agent is actually allowed to do.
- **Copy size:** `--fresh-copy` copies the entire directory including `.git` and e.g. `node_modules`. For large repositories this costs time and disk space.
- **Format changes:** The evaluation tolerates missing fields and non-JSON lines. If OpenCode fundamentally changes the event types, individual columns will stay empty. The raw data in `events.jsonl` is always kept.

## Troubleshooting

| Symptom | Cause and solution |
|---|---|
| `opencode not found in PATH` | Install OpenCode or extend the `PATH`. |
| `expected one argument` for `-p` | The prompt starts with `-`. Use `--prompt="…"` instead. |
| `accounting_source = none`, `status = error` | Check the run's `stderr.log`. Common causes are a missing API key, an invalid model, or access denied by the nono profile. |
| Runs abort immediately, nono messages in `stderr.log` | The profile does not allow required paths or hosts. Derive your own profile with `nono profile init … --extends …` and extend it. |
| Runs hang until the timeout | OpenCode is probably waiting for a permission approval (see [Notes](#notes-and-limitations)). |
| Warning about a differing header | The existing CSV uses a different delimiter or comes from an older version. Use the same `-d` as when it was created, or choose a new file. |
| Excel shows everything in one column | Write with `-d ';'` or import in Excel via *Data → From Text/CSV*. |

## License

Released under the [MIT License](LICENSE).
