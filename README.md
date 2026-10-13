# OpenCode-Multirun

Pilot study for a master's thesis: **How does a coding agent handle a prompt and the knowledge that is provided to it?**

The agent ([OpenCode](https://opencode.ai) with a local model) gets a task on a small database project. The task stays the same, the knowledge changes: no guidelines, one guideline, an extended set, a conflicting set, and the same guidelines through an MCP server instead of files. Every combination is run several times. A small script runs the agent and records quantitative metrics; the results of the agent are compared with a known ground truth afterwards.

## Study design

| | |
|---|---|
| **Task** (prompt) | `review-schema` (find violations), `add-tables` (write new migration), `fix-feed-table` (rework a table) |
| **Knowledge** (condition) | `none`, `base`, `standards`, `all` (conflicting rules), `mcp` (all guidelines through an MCP server) |
| **Object** | a PostgreSQL schema (`sample_project/`) that deliberately violates the guidelines |
| **Repetitions** | several runs per combination, because the output of an agent varies |
| **Model** | a local model served by Ollama |

| Condition | The agent gets |
|---|---|
| `none` | nothing besides the task |
| `base` | `database-guidelines.md` as file in the workspace |
| `standards` | the base guideline plus `database-standards.md` |
| `all` | all three guideline files, including `database-design-conventions.md` |
| `mcp` | all three guidelines through the `docs` MCP server (no files) |

What the guidelines contain and how they relate to each other is deliberately **not** stated in the guideline files. It is documented in the ground truth (see below).

## Repository layout

| Path | Content |
|---|---|
| `tools/opencode_multirun.py` | the measuring tool: runs a prompt n times and records metrics |
| `study/prompts/` | the tasks |
| `study/config/` | OpenCode configuration and project notes that are copied into the workspace |
| `study/run.sh` | runs one condition with one prompt |
| `study/index-knowledge.sh` | indexes the guidelines into the MCP server |
| `study/ground-truth/violations.md` | every built-in violation and the conflicts between the guidelines |
| `sample_project/` | the database project the agent works on |
| `sample_guidelines/` | the guidelines (knowledge) |
| `docker-compose.yml` | Ollama with two models and the docs MCP server |
| `results/` | output of the runs (not in git) |

`study/ground-truth/` must never be copied into a workspace or shown to an agent.

## Setup

Requirements: Docker, [OpenCode](https://opencode.ai), Python ≥ 3.9, git. Linux, macOS or WSL2.

```bash
cp .env.example .env              # optional: choose the models
docker compose up -d              # Ollama (coding and embedding model) and the MCP server
docker compose logs -f ollama-pull  # the first start downloads the models
study/index-knowledge.sh          # only needed for the condition "mcp"
```

The defaults are `qwen2.5-coder:7b` (coding) and `nomic-embed-text` (embeddings). The context window of Ollama is raised to 32k tokens, because tool calls are unreliable with the default.

## Run an experiment

```bash
study/run.sh <condition> <prompt> [runs]
```

```bash
study/run.sh none review-schema 5
study/run.sh base review-schema 5
study/run.sh all add-tables 5
MODEL=ollama/qwen2.5-coder:14b study/run.sh mcp fix-feed-table 3
```

Each run works on its **own copy** of `sample_project/`, so runs are independent and the original is never changed. The knowledge of the condition is added to the copy. Everything after the third argument is passed to the tool, e.g. `-t 3600` for a longer time limit.

To use the tool directly:

```bash
tools/opencode_multirun.py -f study/prompts/review-schema.md -n 5 -m ollama/qwen2.5-coder:7b \
  -w sample_project --label base \
  --add study/config/opencode.json:opencode.json \
  --add sample_guidelines/database-guidelines.md:guidelines/
```

| Option | Meaning |
|---|---|
| `-f`, `--prompt-file` | file with the prompt (required) |
| `-n`, `--runs` | number of runs (default 1) |
| `-m`, `--model` | model, e.g. `ollama/qwen2.5-coder:7b` |
| `-w`, `--workdir` | directory that is copied for every run (default: current directory) |
| `--add SRC[:DEST]` | copy a file or directory into every workspace; with a trailing `/` DEST is a directory |
| `--label` | name of the condition |
| `-o`, `--out` | output directory (default `results`) |
| `-t`, `--timeout` | time limit per run in seconds (default 1800) |

## Results

```
results/
├── runs.csv                 one row per run
└── <batch>/run-001/
    ├── response.txt         final answer of the agent (e.g. the review report)
    ├── changes.patch        everything the agent changed in the workspace
    ├── events.jsonl         complete event stream of OpenCode
    ├── stderr.log, export.json, command.txt
    └── workspace/           the working copy after the run
```

`runs.csv` contains these columns:

| Group | Columns |
|---|---|
| Identification | `batch_id`, `run_index`, `label` (condition), `prompt`, `model_requested`, `model_effective`, `session_id`, `prompt_sha256`, `opencode_version`, `run_dir` |
| Time and status | `start_utc`, `end_utc`, `duration_s`, `status` (`ok`, `error`, `timeout`), `exit_code`, `error_message` |
| Tokens and cost | `steps`, `tokens_total`, `tokens_input`, `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`, `cost_usd`, `accounting_source` |
| Behavior | `tool_calls`, `tool_errors`, `tools_used` (`;`-separated, MCP tools show up with their name), `output_chars` |
| Changes | `files_changed`, `lines_added`, `lines_deleted` |

Tokens and cost come from the event stream. Because the last event is missing in some OpenCode versions, the tool also reads `opencode export` and uses it if it is more complete (`accounting_source`). With local models `cost_usd` is `0`; tokens are still counted.

Example analysis:

```python
import pandas as pd

df = pd.read_csv("results/runs.csv")
print(df.groupby(["prompt", "label"])[["tokens_total", "duration_s", "tool_calls", "lines_added"]]
        .agg(["mean", "std"]).round(1))
print(df.groupby(["prompt", "label"]).status.value_counts().unstack(fill_value=0))
```

## Evaluation against the ground truth

The quantitative metrics describe the effort of the agent, not the quality of its result. For the quality, compare `response.txt` (review) or `changes.patch` (new migration) with `study/ground-truth/violations.md`. It lists every built-in violation of the schema by rule and by table, and how the three guidelines relate to each other.

## Notes

- **Local models vary.** Use several runs per combination and look at the spread (`std`), not only at the mean.
- **Permission prompts.** A non-interactive run can hang if OpenCode asks for permission; the time limit ends such runs with the status `timeout`.
- **MCP condition.** The indexing of the guidelines (`study/index-knowledge.sh`) needs the running stack and the embedding model. If the MCP server does not respond, check `http://localhost:6280`.
- **Reproducibility.** The tool stores the exact command, the prompt hash and the versions with every run.

## License

Released under the [MIT License](LICENSE).
