# OpenCode-Multirun

Pilot study for a master's thesis: **How does a coding agent handle a prompt and the knowledge that is provided to it?**

The agent ([OpenCode](https://opencode.ai) with a language model) gets a task on a small database project. The task stays the same, the knowledge changes: no guidelines, one guideline, an extended set, a conflicting set, and the same guidelines through an MCP server instead of files. Every combination is run several times. A small script runs the agent and records quantitative metrics; the results of the agent are compared with a known ground truth afterwards.

## Study design

| | |
|---|---|
| **Task** (prompt) | `review-schema` (find violations), `add-tables` (write new migration), `fix-feed-table` (rework a table) |
| **Knowledge** (condition) | `none`, `base`, `standards`, `all` (conflicting rules), `mcp` (all guidelines through an MCP server) |
| **Object** | a PostgreSQL schema (`sample_project/`) that deliberately violates the guidelines |
| **Repetitions** | several runs per combination, because the output of an agent varies |
| **Model** | one model for all conditions, default `github-copilot/claude-sonnet-5` |

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
| `study/setup-ollama.sh` | pulls the embedding model into the local Ollama (condition `mcp`) |
| `docker-compose.yml` | the docs MCP server (condition `mcp`) |
| `results/` | output of the runs (not in git) |

`study/ground-truth/` must never be copied into a workspace or shown to an agent.

## Setup

Requirements:

| Requirement | Used for |
|---|---|
| [OpenCode](https://opencode.ai) **2.x** | the agent under test |
| A model provider that OpenCode supports, e.g. GitHub Copilot | the language model of the agent |
| Python ≥ 3.9 and git | the measuring tool |
| [Ollama](https://ollama.com) and Docker | only for the condition `mcp`: Ollama computes the embeddings, Docker runs the docs MCP server |

Linux, macOS or WSL2.

```bash
opencode auth login          # sign in to the provider of the model (once)
```

For the condition `mcp` additionally:

```bash
study/setup-ollama.sh        # pulls the embedding model into the local Ollama
docker compose up -d         # docs MCP server on http://localhost:6281
study/index-knowledge.sh     # indexes the guidelines into the MCP server
```

The default model is `github-copilot/claude-sonnet-5`. Use another model with `MODEL=<provider>/<model> study/run.sh …` (list: `opencode models`), e.g. `MODEL=ollama/qwen3.5:9b` for a local model that is configured in `study/config/opencode*.json`. A local model needs Ollama with a context window of at least 32k tokens (`OLLAMA_CONTEXT_LENGTH=32768`), otherwise tool calls fail. Ports and the embedding model can be changed in `.env` (see `.env.example`). The MCP server runs on host port **6281**, because 6280 is often taken by another docs-mcp-server; it reaches Ollama through `host.docker.internal`.

## Run an experiment

```bash
study/run.sh <condition> <prompt> [runs]
```

```bash
study/run.sh none review-schema 5
study/run.sh base review-schema 5
study/run.sh all add-tables 5
MODEL=github-copilot/claude-haiku-5.5 study/run.sh mcp fix-feed-table 3
```

Each run works on its **own copy** of `sample_project/`, so runs are independent and the original is never changed. The knowledge of the condition is added to the copy. Everything after the third argument is passed to the tool, e.g. `-t 3600` for a longer time limit.

To use the tool directly:

```bash
tools/opencode_multirun.py -f study/prompts/review-schema.md -n 5 -m github-copilot/claude-sonnet-5 \
  -w sample_project --label base \
  --add study/config/opencode.json:opencode.json \
  --add sample_guidelines/database-guidelines.md:guidelines/
```

| Option | Meaning |
|---|---|
| `-f`, `--prompt-file` | file with the prompt (required) |
| `-n`, `--runs` | number of runs (default 1) |
| `-m`, `--model` | model, e.g. `github-copilot/claude-sonnet-5` |
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

Tokens and cost are taken from the stored session (`opencode session export`, `accounting_source = export`); if the export is not available, the event stream is used (`stream`). Only the model calls of the agent are counted, not the generation of the session title. `cost_usd` is the price that OpenCode calculates from the token counts; it is not what a subscription such as GitHub Copilot bills (see Notes). With local models it is `0`.

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

- **Isolated runs.** OpenCode runs in the copy of the project with a private server (`--standalone`) and an empty configuration directory (`XDG_CONFIG_HOME`), so that your personal OpenCode configuration (MCP servers, plugins, rules, agents) does not influence the study. The agent only sees the `opencode.json` and `AGENTS.md` that the condition puts into the workspace. Rule files above the workspace (such as this repository's `AGENTS.md`) are not read, because every workspace is its own git repository. Only your provider credentials are shared.
- **Fixed environment.** `study/config/opencode*.json` disable automatic updates, sharing of sessions and the web tools (`webfetch`, `websearch`), so that the agent cannot look up knowledge on the internet. The version of OpenCode is stored with every run (`opencode_version`); do not update it during a series.
- **Permissions.** The runs use `--auto`: the agent may run shell commands and change files without asking, otherwise unattended runs would wait for an answer forever. Only access to directories outside of the workspace is denied by the configuration. The shell is not sandboxed, so do not run the study with a model or a prompt you do not trust on a machine with sensitive data (a container or virtual machine is safer).
- **Models vary.** The output of an agent differs from run to run. Use several runs per combination and look at the spread (`std`), not only at the mean. Use fixed model names, not aliases like `-latest`.
- **Subscriptions.** With a subscription such as GitHub Copilot the cost is not paid per token. Check how many premium requests a run uses (a run has several model calls, see `steps`) before you start a large series, and watch the usage limits of the provider.
- **MCP condition.** The indexing (`study/index-knowledge.sh`) needs Ollama with the embedding model and the running MCP server. If the server does not respond, check `http://localhost:6281`.
- **Tool calls.** Small models sometimes write a tool call as plain text instead of calling the tool. The run then ends after one step without any tool call (see `response.txt`, `tool_calls = 0`). Such runs count as results of the model; choose a model that supports tools reliably.
- **Reproducibility.** The tool stores the exact command, the prompt hash and the versions with every run.

## License

Released under the [MIT License](LICENSE).
