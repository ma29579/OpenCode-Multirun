# OpenCode-Multirun

Pilot study for a master's thesis: **How does a coding agent handle a prompt and the knowledge that is provided to it?**

The agent ([OpenCode](https://opencode.ai) with a language model) gets a task on a small database project. The task stays the same, the knowledge changes: no knowledge, the rules inside `AGENTS.md`, as plain files, as specs (spec-driven), through an MCP server, and a hybrid of MCP server and specs. Every combination is run several times. A script runs the agent and records quantitative metrics; a linter checks how well the result follows the rules.

## Study design

| | |
|---|---|
| **Task** (prompt) | `add-tables` (customer tables), `add-animals` (poultry tables), `fix-feed-table` (rework a table and its data), `urgent-fix` (make a column optional on production), `review-schema` (find violations) |
| **Knowledge** (scenario) | six ways to provide the same 32 rules, see below |
| **Object** | a PostgreSQL schema (`sample_project/`) that deliberately violates the rules |
| **Repetitions** | several runs per combination, because the output of an agent varies |
| **Models** | two models from different vendors, the same for all scenarios: `github-copilot/claude-sonnet-5` and `github-copilot/gpt-5.5` (list: `opencode models`) |

The 32 rules come from three guideline documents in `sample_guidelines/`: `DB` (12 general rules, mostly known to a model, they serve as controls), `STD` (11 house rules that extend them and that a model cannot know) and `DES` (9 plausible conventions that **contradict** a general rule or a house rule on purpose). The documents do not say how they relate; this is only documented in the ground truth (`study/ground-truth/violations.md`).

| Scenario | The agent gets |
|---|---|
| `baseline` | no knowledge, only the task |
| `a-agents-md` | all guidelines inside `AGENTS.md` (in the context of every request) |
| `b-guideline-files` | the three guideline files in `guidelines/`; `AGENTS.md` points to them |
| `c-spec-files` | the rules grouped by requirement as specs in `specs/<capability>/spec.md` (spec-driven development); `AGENTS.md` points to them |
| `d-mcp-server` | the three guideline files through the `docs` MCP server (no files) |
| `e-mcp-and-specs` | the **general** guidelines (`DB`, 12 rules: static knowledge) through the MCP server, the **project-specific** rules (`STD` and `DES`, 20 rules: dynamic knowledge) as specs in `specs/` |

In `c-spec-files` and `e-mcp-and-specs` the rules are grouped by topic (capability), not by source document, so contradicting rules stand next to each other (in `e-mcp-and-specs` the general guidelines are in the MCP server and the contradicting rules in the specs). Static knowledge is general and rarely changes; dynamic knowledge is specific to the project and lives next to the code. The assignment of the rules to capabilities is in `study/build-scenarios.py`.

## Repository layout

| Path | Content |
|---|---|
| `tools/opencode_multirun.py` | the measuring tool: runs a prompt n times and records metrics |
| `tools/schema_lint.py` | the linter: checks the schema that an agent produced against the rules |
| `study/prompts/` | the tasks |
| `study/build-scenarios.py` | builds the scenarios in `study/scenarios/` from the guidelines |
| `study/run-all.sh` | runs the whole study: every scenario with every prompt, then the linter |
| `study/run.sh` | runs one scenario with one prompt |
| `study/index-knowledge.sh` | indexes the guidelines into the two MCP servers |
| `study/config/opencode.json` | OpenCode configuration that every scenario starts from |
| `study/ground-truth/violations.md` | every built-in violation and the conflicts between the guidelines |
| `sample_project/` | the database project the agent works on |
| `sample_guidelines/` | the guidelines (the source of all scenarios) |
| `study/setup-ollama.sh` | pulls the embedding model into the local Ollama (MCP scenarios) |
| `docker-compose.yml` | the two docs MCP servers (scenarios `d-mcp-server`, `e-mcp-and-specs`) |
| `results/` | output of the runs (not in git) |

`study/ground-truth/` must never be copied into a workspace or shown to an agent.

## Setup

Requirements:

| Requirement | Used for |
|---|---|
| [OpenCode](https://opencode.ai) **2.x** | the agent under test |
| A model provider that OpenCode supports, e.g. GitHub Copilot | the language model of the agent |
| Python ≥ 3.9 and git | the measuring tool |
| Docker | the MCP servers and the linter (a throw-away PostgreSQL) |
| [Ollama](https://ollama.com) | only for the MCP scenarios: computes the embeddings |

Linux, macOS or WSL2.

```bash
opencode auth login          # sign in to the provider of the model (once)
study/setup-ollama.sh        # pulls the embedding model into the local Ollama
docker compose up -d         # MCP servers: all rules on :6281, general guidelines only on :6282
study/index-knowledge.sh     # builds the scenarios and indexes the rules into both servers
```

The default models are `github-copilot/claude-sonnet-5` and `github-copilot/gpt-5.5`. Use others with `MODELS="<provider>/<model> …" study/run-all.sh …` (list: `opencode models`); `study/run.sh` takes a single model in `MODEL`. Ports and the embedding model can be changed in `.env` (see `.env.example`); run `study/build-scenarios.py` again afterwards, it writes the ports into the scenarios. The servers reach Ollama through `host.docker.internal`. They are separate, so that the agent of `d-mcp-server` cannot see the specific rules and the agent of `e-mcp-and-specs` cannot see all rules.

## Run the study

```bash
study/run-all.sh [runs]      # default 3 runs per combination
```

This runs 2 models × 6 scenarios × 5 prompts × `runs` agent runs (180 with the default), writes everything to `results/study-<timestamp>/` and finishes with the linter. Check the quota of your provider first (see Notes). Restrict the study with environment variables:

```bash
SCENARIOS="baseline b-guideline-files" PROMPTS=add-tables study/run-all.sh 5
MODELS=github-copilot/claude-haiku-5.5 study/run-all.sh 3
```

One combination:

```bash
study/run.sh <scenario> <prompt> [runs]        # e.g. study/run.sh c-spec-files add-tables 3
```

Each run works on its **own copy** of `sample_project/`, so runs are independent and the original is never changed. The files of the scenario are added to the copy. To use the tool directly, see `tools/opencode_multirun.py --help`. A run is stopped after 30 minutes (`TIMEOUT_SEC` in the tool).

| Option of the tool | Meaning |
|---|---|
| `-f`, `--prompt-file` | file with the prompt (required) |
| `-n`, `--runs` | number of runs (default 1) |
| `-m`, `--model` | model, e.g. `github-copilot/claude-sonnet-5` |
| `-w`, `--workdir` | directory that is copied for every run (default: current directory) |
| `--add SRC[:DEST]` | copy a file or directory into every workspace; with a trailing `/` DEST is a directory |
| `--label` | name of the scenario |
| `-o`, `--out` | output directory (default `results`) |

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
| Identification | `batch_id`, `run_index`, `label` (scenario), `prompt`, `model_requested`, `model_effective`, `session_id`, `prompt_sha256`, `opencode_version`, `run_dir` |
| Time and status | `start_utc`, `end_utc`, `duration_s`, `status` (`ok`, `error`, `timeout`), `exit_code`, `error_message` |
| Tokens and cost | `steps`, `tokens_total`, `tokens_input`, `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`, `cost_usd`, `accounting_source` |
| Behavior | `tool_calls`, `tool_errors`, `mcp_calls`, `tools_used` (`;`-separated), `output_chars` |
| Use of the knowledge | `sql_files_read` (how many SQL files the agent read), `guideline_files_read` (how many files in `guidelines/` or `specs/` it read), `knowledge_accessed` (`1` if it read such a file or called the MCP server, otherwise `0`; always `0` in `a-agents-md` and `baseline`, because `AGENTS.md` is part of the context of the agent anyway) |
| Changes | `files_changed`, `lines_added`, `lines_deleted` |

In OpenCode 2 an agent calls MCP tools from code with the tool `execute` (`tools.<server>.<tool>(…)`). `mcp_calls` counts these references in the code of all `execute` calls, and `tools_used` lists them as `<server>.<tool>` (e.g. `docs.search_docs`). A call in a loop is counted once, so the value tells whether and how the MCP server was used, not how often it was queried. `knowledge_accessed` shows whether the agent used the provided knowledge at all; the content it got and applied has to be evaluated from `response.txt`. `sql_files_read` shows how much of the schema the agent looked at (the sample project has 8 SQL files).

Tokens and cost are taken from the stored session (`opencode session export`, `accounting_source = export`); if the export is not available, the event stream is used (`stream`). Only the model calls of the agent are counted, not the generation of the session title. `cost_usd` is the price that OpenCode calculates from the token counts; it is not what a subscription such as GitHub Copilot bills (see Notes). With local models it is `0`.

Example analysis:

```python
import pandas as pd

df = pd.read_csv("results/runs.csv")
print(df.groupby(["prompt", "label"])[["tokens_total", "duration_s", "tool_calls", "lines_added"]]
        .agg(["mean", "std"]).round(1))
print(df.groupby(["prompt", "label"]).status.value_counts().unstack(fill_value=0))
```

## Linter: the quality of the result

The metrics of `runs.csv` describe the effort of the agent, not the quality of its result. The linter turns the quality into numbers:

```bash
python3 tools/schema_lint.py results/study-<timestamp>      # run-all.sh does this at the end
```

For every run it applies the migrations of the workspace (`db/migrations/V*.sql`, in version order) to a fresh PostgreSQL in a Docker container, reads the schema from the catalog and checks all 32 rules. Only the tables, views and files that the agent **created or changed** are scored; the violations that the sample project already has do not count against the agent. A rule is *satisfied* if all its checks on these objects pass, and *applicable* if the agent created at least one object it applies to.

| Column of `lint.csv` | Meaning |
|---|---|
| `applied` | `1` if all migrations apply without error (`error` holds the message) |
| `touched` | number of tables, views and files that the agent created or changed |
| `db_rate`, `std_rate` | satisfied rules / applicable rules of the base guideline and the standards |
| `des_rate` | adopted conflicting conventions / applicable ones; a high value means that the agent followed the contradicting guideline (`adopted_des` lists them) |
| `*_applicable`, `*_satisfied`, `*_checks`, `*_passed` | the counts behind the rates; a *check* is one column, constraint or table |
| `violations_baseline`, `violations_result` | violations of `DB` and `STD` in the whole schema before and after the run |
| `regressions` | checks that passed before and fail now |
| `failed_rules` | `DB`/`STD` rules that were violated on the new or changed objects |

`<run_dir>/lint.json` lists every single check. The linter measures only runs that change the schema (all prompts except `review-schema`); the review is evaluated from `response.txt`. Several checks are heuristics, for example which column holds an enumeration or a quantity (names and types); they are validated against the ground truth: on the unchanged sample project the linter finds the violations listed there. Rules about reasoning (for example "natural keys are unique") are checked for the cases that can be decided from the schema. The linter and the guidelines must have the same rule IDs; the linter stops otherwise.

Example analysis:

```python
import pandas as pd

lint = pd.read_csv("results/study-.../lint.csv")
print(lint.groupby(["prompt", "label"])[["db_rate", "std_rate", "des_rate"]].mean().round(2))
```

## Notes

- **Isolated runs.** OpenCode runs in the copy of the project with a private server (`--standalone`) and an empty configuration directory (`XDG_CONFIG_HOME`), so that your personal OpenCode configuration (MCP servers, plugins, rules, agents) does not influence the study. The agent only sees the `opencode.json` and `AGENTS.md` that the scenario puts into the workspace. Rule files above the workspace (such as this repository's `AGENTS.md`) are not read, because every workspace is its own git repository. Only your provider credentials are shared.
- **Fixed environment.** `study/config/opencode*.json` disable automatic updates, sharing of sessions and the web tools (`webfetch`, `websearch`), so that the agent cannot look up knowledge on the internet. The version of OpenCode is stored with every run (`opencode_version`); do not update it during a series.
- **Permissions.** The runs use `--auto`: the agent may run shell commands and change files without asking, otherwise unattended runs would wait for an answer forever. Only access to directories outside of the workspace is denied by the configuration. The shell is not sandboxed, so do not run the study with a model or a prompt you do not trust on a machine with sensitive data (a container or virtual machine is safer).
- **Models vary.** The output of an agent differs from run to run. Use several runs per combination and look at the spread (`std`), not only at the mean. Use fixed model names, not aliases like `-latest`.
- **Subscriptions.** With a subscription such as GitHub Copilot the cost is not paid per token. Check how many premium requests a run uses (a run has several model calls, see `steps`) before you start a large series, and watch the usage limits of the provider.
- **MCP scenarios.** The indexing (`study/index-knowledge.sh`) needs Ollama with the embedding model and the running MCP servers. If a server does not respond, check `http://localhost:6281` (all rules) and `http://localhost:6282` (general guidelines only).
- **Tool calls.** Small models sometimes write a tool call as plain text instead of calling the tool. The run then ends after one step without any tool call (see `response.txt`, `tool_calls = 0`). Such runs count as results of the model; choose a model that supports tools reliably.
- **Reproducibility.** The tool stores the exact command, the prompt hash and the versions with every run.

## License

Released under the [MIT License](LICENSE).
