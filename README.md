# OpenCode-Multirun

Pilot study for a master's thesis: **How does a coding agent handle a prompt and the knowledge that is provided to it?**

A coding agent ([OpenCode](https://opencode.ai) or Claude Code, with a language model) gets a task on a small PostgreSQL project. The task stays the same, the knowledge changes: it is provided in different forms and through different channels, and part of it contradicts the rest on purpose. Every combination is run several times. A script runs the agent and records quantitative metrics; a linter turns the quality of the result into numbers; a second model call evaluates what the agent says about conflicting rules.

## Research questions

1. Does provided knowledge improve how well the result follows the rules, compared with no knowledge (`baseline`)?
2. Does the form of the knowledge matter: inside `AGENTS.md`, as plain files, as specs (spec-driven development), through an MCP server?
3. What happens when the knowledge is split over two channels, and when the **contradicting** knowledge reaches the agent through another channel than the **target** knowledge?
4. Does the agent notice a conflict between two rules, decide, and say so, or does it follow one side by chance?
5. Do the answers depend on the model and on the harness (the program around the model)?

## Study design

| Factor | Levels |
|---|---|
| **Task** (prompt) | five tasks, see below |
| **Knowledge** (scenario) | nine ways to provide the same 32 rules, see below |
| **Model** | `github-copilot/claude-sonnet-5` and `github-copilot/gpt-5.5` (two vendors); more with `MODELS` (list: `opencode models`) |
| **Harness** | OpenCode (default) and Claude Code (`--harness claude`, planned for a subset, see [Procedure](#procedure)) |
| **Repetitions** | several runs per combination, because the output of an agent varies |
| **Object** | a PostgreSQL schema (`sample_project/`) that deliberately violates the rules |

The task, the prompt and the project are the same in every scenario; only the provided knowledge differs. A prompt never names a guideline, a spec or a file.

### Tasks

| Task | The agent has to … | Intention |
|---|---|---|
| `add-tables` | write a migration `V8` with customer and order tables | the standard case, build new tables by the rules; touches most house rules (`PII:` comments, `is_` prefix, currency suffix) and several conflicts (singular names, UUID keys, lookup table for the status) |
| `add-animals` | write a migration `V8` with tables for chickens, ducks and geese | structure between related tables: one table per species (`DB-10`) against one shared table (`DES-07`), units in names, audit columns, join tables |
| `fix-feed-table` | rework the table `feed` and everything that depends on it with new migrations, migrate the data | repairing instead of building; the hardest task (rename, change types, copy data, recreate views) |
| `urgent-fix` | make `feed_deliveries.supplier_id` nullable, urgently, on production | a small change under time pressure; shows whether the agent writes a versioned migration (`DB-12`) or a hotfix script (`DES-09`); only the changed checks are scored |
| `review-schema` | review the schema against the rules and report every violation, without changing files | the knowledge as a yardstick instead of a guide; evaluated from the answer, not by the linter |

### Rules

The 32 rules come from three guideline documents in `sample_guidelines/`. The documents do not say how they relate; this is only documented in the ground truth (`study/ground-truth/violations.md`).

| Document | Rules | Role |
|---|---|---|
| `database-guidelines.md` | `DB-01` … `DB-12` | general rules, mostly known to a model; **target** knowledge and the controls |
| `database-standards.md` | `STD-01` … `STD-11` | house rules that a model cannot know; **target** knowledge |
| `database-design-conventions.md` | `DES-01` … `DES-09` | plausible alternatives that **contradict** a general rule or a house rule on purpose; **misleading** knowledge |

### Scenarios

| Scenario | MCP server | Files in the workspace |
|---|---|---|
| `baseline` | – | – (no knowledge) |
| `a-agents-md` | – | all guidelines inside `AGENTS.md`, i.e. in the context of every request |
| `b-guideline-files` | – | the three guideline files in `guidelines/`; `AGENTS.md` points to them |
| `c-spec-files` | – | all rules grouped by topic as specs in `specs/<capability>/spec.md` (spec-driven development) |
| `d-mcp-server` | all three guidelines (port 6281) | – |
| `e-mcp-and-specs` | `DB` (6282) | `STD` and `DES` as specs |
| `f-split-spec-files` | – | all rules as specs, separated by source: `specs/general/` (`DB`), `specs/project/` (`STD`, `DES`) |
| `g-target-mcp-conflict-specs` | `DB` and `STD` (6283) | `DES` as specs |
| `h-conflict-mcp-target-specs` | `DES` (6284) | `DB` and `STD` as specs |

In `c`, `e`, `f`, `g` and `h` the rules are grouped by topic (capability), so contradicting rules stand next to each other where they are in the same channel. The assignment of the rules to capabilities is in `study/build-scenarios.py`.

Which comparison answers which question:

| Comparison | Question |
|---|---|
| `baseline` against every other scenario | 1: does knowledge help at all, and for which rules |
| `a`, `b`, `c`, `d` | 2: form and channel of the same rules (one channel each) |
| `c` against `f` | 3: does the separation by source matter, with the same channel |
| `d` against `e` | 3: does splitting the knowledge over two channels matter |
| `g` against `h` | 3: where does the misleading knowledge hurt more, in the files or in the MCP server |
| `g`, `h` against `c`, `d` | 3: the cost of separating target and misleading knowledge compared with one channel |

### Measures

| What | How | Where |
|---|---|---|
| Effort | tokens, duration, steps, tool calls, MCP calls, files read, size of the change | `runs.csv` (the tool) |
| Use of the knowledge | `knowledge_accessed`, `guideline_files_read`, `mcp_calls` | `runs.csv` |
| Quality of the result | share of satisfied rules on the new or changed objects, split into `DB`, `STD` and `DES` (adopted conflicting conventions) | `lint.csv` (the linter) |
| Behavior at a conflict | does the agent name the contradiction, explain its decision, say which side it follows, claim full compliance | `judge.csv` (second model call) |
| Validity of the linter | blind manual rating of a sample, agreement and Cohen's kappa | `tools/validate_lint.py` |
| Statistics | mean, 95% bootstrap interval, permutation test against `baseline` with Holm correction | `tools/analyze.py` |

### Procedure

1. **Run** the study with OpenCode and two models: `study/run-all.sh [runs]`. The linter runs at the end.
2. **Judge** the answers: `python3 tools/judge_responses.py <results>` (one call of a model of another family per run, see below).
3. **Validate** the linter by hand with a blind sample and a second rater: `tools/validate_lint.py`.
4. **Analyze**: `python3 tools/analyze.py <results>`. With two runs per combination no p-value can be small; the statistics are meant for effect sizes and to plan the number of runs.
5. **Check the harness** on a small subset with Claude Code (and later Codex), with the same model as in OpenCode so that the effect of the harness can be separated from the effect of the model; suggested subset: scenarios `baseline`, `a`, `b`, `d`, `e` and tasks `add-tables`, `urgent-fix`. Replicate the findings of step 4 only where they exist.

### Status and limitations

- The scenarios `baseline` to `e` have run with two models and two runs per combination as a first test; `f`, `g` and `h` are built and indexed but have not run with agents yet. There are no final results. The pilot is meant to find problems of the design and to plan the main study.
- One synthetic SQL project: the findings are valid for this project, not for software conventions in general.
- The linter works with heuristics on names and types (which column holds an enumeration or a quantity) and is checked against the ground truth and, with `validate_lint.py`, by hand. The judge is a model as well; check a sample of its verdicts.
- The design was adapted after the first runs (rules, prompts, linter). For the main study fix the hypotheses and the measures before the first run.
- The order of the runs is fixed and not randomized, and model versions behind a provider name can change.
- Absolute numbers of different harnesses are not comparable one to one.

## Repository layout

| Path | Content |
|---|---|
| `tools/opencode_multirun.py` | the measuring tool: runs a prompt n times and records metrics |
| `tools/schema_lint.py` | the linter: checks the schema that an agent produced against the rules |
| `tools/validate_lint.py` | blind manual rating of a sample of linter checks, agreement and Cohen's kappa |
| `tools/judge_responses.py` | second model call: what the agents say about conflicting rules |
| `tools/analyze.py` | statistics: mean, bootstrap interval and permutation test against the baseline |
| `study/prompts/` | the tasks |
| `study/build-scenarios.py` | builds the scenarios in `study/scenarios/` from the guidelines |
| `study/run-all.sh` | runs the whole study: every scenario with every prompt, then the linter |
| `study/run.sh` | runs one scenario with one prompt |
| `study/index-knowledge.sh` | indexes the guidelines into the four MCP servers |
| `study/config/opencode.json` | OpenCode configuration that every scenario starts from |
| `study/ground-truth/violations.md` | every built-in violation and the conflicts between the guidelines |
| `sample_project/` | the database project the agent works on |
| `sample_guidelines/` | the guidelines (the source of all scenarios) |
| `study/setup-ollama.sh` | pulls the embedding model into the local Ollama (MCP scenarios) |
| `docker-compose.yml` | the four docs MCP servers (scenarios `d-mcp-server`, `e-mcp-and-specs`, `g-target-mcp-conflict-specs`, `h-conflict-mcp-target-specs`) |
| `results/` | output of the runs (not in git) |

`study/ground-truth/` must never be copied into a workspace or shown to an agent.

## Setup

Requirements:

| Requirement | Used for |
|---|---|
| [OpenCode](https://opencode.ai) **2.x** | the agent under test |
| [Claude Code](https://claude.com/claude-code) (`claude`) | optional, a second harness |
| A model provider that OpenCode supports, e.g. GitHub Copilot | the language model of the agent |
| Python ≥ 3.9 and git | the measuring tool |
| Docker | the MCP servers and the linter (a throw-away PostgreSQL) |
| [Ollama](https://ollama.com) | only for the MCP scenarios: computes the embeddings |

Linux, macOS or WSL2.

```bash
opencode auth login          # sign in to the provider of the model (once)
study/setup-ollama.sh        # pulls the embedding model into the local Ollama
docker compose up -d         # MCP servers: all rules on :6281, DB only on :6282, DB and STD on :6283, DES only on :6284
study/index-knowledge.sh     # builds the scenarios and indexes the rules into the four servers
```

The default models are `github-copilot/claude-sonnet-5` and `github-copilot/gpt-5.5`. Use others with `MODELS="<provider>/<model> …" study/run-all.sh …` (list: `opencode models`); `study/run.sh` takes a single model in `MODEL`. Ports and the embedding model can be changed in `.env` (see `.env.example`); run `study/build-scenarios.py` again afterwards, it writes the ports into the scenarios. The servers reach Ollama through `host.docker.internal`. The servers are separate, so that the agent of a scenario only sees the documents that belong to it (e.g. the agent of `e-mcp-and-specs` cannot see `STD` and `DES`).

## Run the study

```bash
study/run-all.sh [runs]      # default 3 runs per combination
```

This runs 2 models × 9 scenarios × 5 prompts × `runs` agent runs (270 with the default), writes everything to `results/study-<timestamp>/` and finishes with the linter. Check the quota of your provider first (see Notes). Restrict the study with environment variables:

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
| `--harness` | the coding agent: `opencode` (default) or `claude` (Claude Code) |
| `-o`, `--out` | output directory (default `results`) |

## Results

```
results/
├── runs.csv                 one row per run
└── <batch>/run-001/
    ├── response.txt         final answer of the agent (e.g. the review report)
    ├── changes.patch        everything the agent changed in the workspace
    ├── events.jsonl         complete event stream of the agent
    ├── stderr.log, export.json, command.txt
    └── workspace/           the working copy after the run
```

`runs.csv` contains these columns:

| Group | Columns |
|---|---|
| Identification | `batch_id`, `run_index`, `label` (scenario), `prompt`, `model_requested`, `model_effective`, `session_id`, `prompt_sha256`, `harness`, `harness_version`, `run_dir` |
| Time and status | `start_utc`, `end_utc`, `duration_s`, `status` (`ok`, `error`, `timeout`), `exit_code`, `error_message` |
| Tokens and cost | `steps`, `tokens_total`, `tokens_input`, `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`, `cost_usd`, `accounting_source` |
| Behavior | `tool_calls`, `tool_errors`, `mcp_calls`, `tools_used` (`;`-separated), `output_chars` |
| Use of the knowledge | `sql_files_read` (how many SQL files the agent read), `guideline_files_read` (how many files in `guidelines/` or `specs/` it read), `knowledge_accessed` (`1` if it read such a file or called the MCP server, otherwise `0`; always `0` in `a-agents-md` and `baseline`, because `AGENTS.md` is part of the context of the agent anyway) |
| Changes | `files_changed`, `lines_added`, `lines_deleted` |

In OpenCode 2 an agent calls MCP tools from code with the tool `execute` (`tools.<server>.<tool>(…)`); in Claude Code they are separate tools named `mcp__<server>__<tool>`. `mcp_calls` counts these references in the code of all `execute` calls, and `tools_used` lists them as `<server>.<tool>` (e.g. `docs.search_docs`). A call in a loop is counted once, so the value tells whether and how the MCP server was used, not how often it was queried. `knowledge_accessed` shows whether the agent used the provided knowledge at all; the content it got and applied has to be evaluated from `response.txt`. `sql_files_read` shows how much of the schema the agent looked at (the sample project has 8 SQL files).

Tokens and cost are taken from the stored session (`opencode session export`, `accounting_source = export`); if the export is not available, the event stream is used (`stream`). Only the model calls of the agent are counted, not the generation of the session title. `cost_usd` is the price that OpenCode calculates from the token counts; it is not what a subscription such as GitHub Copilot bills (see Notes).

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

For `urgent-fix`, which changes one spot of an existing table, only the checks that are new or whose result changed are scored (`NARROW_PROMPTS` in the linter); otherwise the agent would be held responsible for the existing columns of the table. `<run_dir>/lint.json` lists every single check. The linter measures only runs that change the schema (all prompts except `review-schema`); the review is evaluated from `response.txt`. Several checks are heuristics, for example which column holds an enumeration or a quantity (names and types); they are validated against the ground truth: on the unchanged sample project the linter finds the violations listed there. Rules about reasoning (for example "natural keys are unique") are checked for the cases that can be decided from the schema. The linter and the guidelines must have the same rule IDs; the linter stops otherwise.

Statistics:

```bash
python3 tools/analyze.py results/study-A results/study-B      # one or more studies with a lint.csv
```

For every task, model and scenario it prints the mean of `db_rate`, `std_rate` and `des_rate` with a 95% bootstrap interval and the Holm-corrected p-value of a permutation test against `baseline` (`*` for p < 0.05), and writes `analysis.csv`. With few runs no p-value can be small (two against two runs give at best p = 0.33), so use it to see effect sizes and to plan the number of runs.

### Check the linter by hand

```bash
python3 tools/validate_lint.py sample results/study-A [results/study-B ...]   # draws the checks
python3 tools/validate_lint.py agree  results/study-A                         # after the rating
```

`sample` writes about 190 checks (up to three satisfied and three violated ones per rule) to `rating-sample.csv` without the verdict of the linter, and the verdicts with model and scenario to `rating-key.csv`. One or two people open the workspace and the patch of every row and fill `rater_1` (and `rater_2`) with `1` (rule satisfied for the object), `0` (violated) or `-` (does not apply), without looking at the key. `agree` prints the agreement and Cohen's kappa between linter and raters and between the raters, and lists the disagreements per rule. Report these numbers together with the results.

### What the agents say about conflicts

```bash
python3 tools/judge_responses.py results/study-A
```

A second model (`JUDGE_MODEL`, default `github-copilot/gemini-3.8-flash`, a different family than the agents) reads the task, the final answer, the patch and the rules, without tools, scenario or model name, and answers: does the agent name a contradiction between rules (`conflict_mentioned`, `conflicts`), does it explain its decision (`decision_explained`), which side does it say it follows (`stated_side`) and does it claim that it followed all rules (`claims_full_compliance`). The result is `judge.csv` and a `judge.json` in every run directory (a repeated call does not judge a run twice). Together with the linter this shows whether an agent follows a convention knowingly or by chance. The judge is a model as well: check a sample of its verdicts by hand, and do not use the same model for the judge and for an agent.

Example analysis with pandas:

```python
import pandas as pd

lint = pd.read_csv("results/study-.../lint.csv")
print(lint.groupby(["prompt", "label"])[["db_rate", "std_rate", "des_rate"]].mean().round(2))
```

## Other harness: Claude Code

The study can run with Claude Code instead of OpenCode, e.g. to check that the results do not depend on the harness. Use the same model in both to separate the effect of the harness from the effect of the model: Sonnet 5 in OpenCode (via Copilot) against Claude Code.

```bash
MODELS="claude:claude-sonnet-5" SCENARIOS="baseline b-guideline-files d-mcp-server" PROMPTS=add-tables study/run-all.sh 2
HARNESS=claude MODEL=claude-sonnet-5 study/run.sh baseline add-tables 1       # a single combination
```

In `MODELS` the prefix `claude:` selects the harness, entries without a prefix run in OpenCode. Everything after the harness is the same: scenarios, prompts, linter, statistics, judge. `runs.csv` has the columns `harness` and `harness_version`; the evaluations group by `harness/model`.

What the tool does for Claude Code (`prepare_claude_workspace`, `build_command`, `parse_claude_events`):
- `AGENTS.md` of the scenario becomes `CLAUDE.md`, the MCP servers of `opencode.json` go to an `mcp.json` in the run directory (`--strict-mcp-config`), `opencode.json` is removed from the workspace.
- `claude -p --output-format stream-json --setting-sources project,local`: no user settings, hooks or plugins; `WebFetch` and `WebSearch` are denied like in the OpenCode configuration; `--permission-mode bypassPermissions` lets the agent act without questions, the shell is not sandboxed (see below); no session persistence and no slash commands.
- The environment is cleaned of the variables of a surrounding Claude Code session (`CLAUDE_*`, `ANTHROPIC_BASE_URL`) and automatic memory is switched off. Your credentials stay (`ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, the login of `claude auth login`).
- Tokens and cost come from the `result` event (`accounting_source = stream`); `cost_usd` is the API-equivalent price, a subscription is not billed per token. Tool names differ (`Read`, `Bash`, `Grep`, MCP tools as `mcp__<server>__<tool>`), `mcp_calls` counts every call to an MCP tool.

Limits: run the study from your own terminal, not from inside another Claude Code session (its login and proxy variables do not work for a nested run). A `~/.claude/CLAUDE.md` of yours would still be read by Claude Code; rename it for the time of the study. Claude Code sets its own default for the thinking effort and has its own system prompt and tools, so absolute numbers of the two harnesses are not comparable one to one.

## Notes

- **Isolated runs.** OpenCode runs in the copy of the project with a private server (`--standalone`) and an empty configuration directory (`XDG_CONFIG_HOME`), so that your personal OpenCode configuration (MCP servers, plugins, rules, agents) does not influence the study. The agent only sees the `opencode.json` and `AGENTS.md` that the scenario puts into the workspace. Rule files above the workspace (such as this repository's `AGENTS.md`) are not read, because every workspace is its own git repository. Only your provider credentials are shared.
- **Fixed environment.** `study/config/opencode*.json` disable automatic updates, sharing of sessions and the web tools (`webfetch`, `websearch`), so that the agent cannot look up knowledge on the internet. The version of OpenCode is stored with every run (`harness_version`); do not update it during a series.
- **Permissions.** The runs use `--auto`: the agent may run shell commands and change files without asking, otherwise unattended runs would wait for an answer forever. Only access to directories outside of the workspace is denied by the configuration. The shell is not sandboxed, so do not run the study with a model or a prompt you do not trust on a machine with sensitive data (a container or virtual machine is safer).
- **Models vary.** The output of an agent differs from run to run. Use several runs per combination and look at the spread (`std`), not only at the mean. Use fixed model names, not aliases like `-latest`.
- **Subscriptions.** With a subscription such as GitHub Copilot the cost is not paid per token. Check how many premium requests a run uses (a run has several model calls, see `steps`) before you start a large series, and watch the usage limits of the provider.
- **MCP scenarios.** The indexing (`study/index-knowledge.sh`) needs Ollama with the embedding model and the running MCP servers. If a server does not respond, check `http://localhost:6281` (all rules), `:6282` (`DB`), `:6283` (`DB` and `STD`) and `:6284` (`DES`).
- **Tool calls.** Small models sometimes write a tool call as plain text instead of calling the tool. The run then ends after one step without any tool call (see `response.txt`, `tool_calls = 0`). Such runs count as results of the model; choose a model that supports tools reliably.
- **Reproducibility.** The tool stores the exact command, the prompt hash and the versions with every run.

## License

Released under the [MIT License](LICENSE).
