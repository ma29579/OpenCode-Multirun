# OpenCode-Multirun

Vorstudie für eine Masterarbeit: **Wie geht ein Coding-Agent mit einem Prompt und dem bereitgestellten Wissen um?**

Ein Coding-Agent ([OpenCode](https://opencode.ai) oder Claude Code, jeweils mit einem Sprachmodell) bekommt eine Aufgabe auf einem kleinen PostgreSQL-Projekt. Die Aufgabe bleibt gleich, das Wissen ändert sich: Es wird in unterschiedlichen Formen und über unterschiedliche Kanäle bereitgestellt, und ein Teil davon widerspricht bewusst dem Rest. Jede Kombination wird mehrfach ausgeführt. Ein Skript führt den Agenten aus und erfasst quantitative Metriken, ein Linter macht die Qualität des Ergebnisses zu Zahlen, und ein zweiter Modellaufruf wertet aus, was der Agent über widersprüchliche Regeln sagt.

## Forschungsfragen

1. Verbessert bereitgestelltes Wissen, wie gut das Ergebnis die Regeln einhält, im Vergleich zu keinem Wissen (`baseline`)?
2. Spielt die Form des Wissens eine Rolle: in der `AGENTS.md`, als einfache Dateien, als Specs (Spec-Driven Development) oder über einen MCP-Server?
3. Was passiert, wenn das Wissen auf zwei Kanäle verteilt ist und wenn das **widersprüchliche** Wissen den Agenten über einen anderen Kanal erreicht als das **Ziel-Wissen**?
4. Erkennt der Agent einen Konflikt zwischen zwei Regeln, entscheidet er sich und sagt er das, oder folgt er einer Seite zufällig?
5. Hängen die Antworten vom Modell und vom Harness (dem Programm um das Modell) ab?

## Studiendesign

| Faktor | Stufen |
|---|---|
| **Aufgabe** (Prompt) | fünf Aufgaben, siehe unten |
| **Wissen** (Szenario) | neun Arten, dieselben 32 Regeln bereitzustellen, siehe unten |
| **Modell** | `github-copilot/claude-sonnet-5` und `github-copilot/gpt-5.5` (zwei Anbieter); weitere mit `MODELS` (Liste: `opencode models`) |
| **Harness** | OpenCode (Standard) und Claude Code (`--harness claude`, für eine Teilmenge geplant, siehe [Vorgehen](#vorgehen)) |
| **Wiederholungen** | mehrere Läufe pro Kombination, weil die Ausgabe eines Agenten schwankt |
| **Objekt** | ein PostgreSQL-Schema (`sample_project/`), das die Regeln bewusst verletzt |

Aufgabe, Prompt und Projekt sind in jedem Szenario gleich; nur das bereitgestellte Wissen unterscheidet sich. Ein Prompt nennt nie eine Guideline, ein Spec oder eine Datei.

### Aufgaben

| Aufgabe | Der Agent soll … | Intention |
|---|---|---|
| `add-tables` | eine Migration `V8` mit Kunden- und Bestelltabellen schreiben | der Standardfall, neue Tabellen nach den Regeln bauen; berührt die meisten Hausregeln (`PII:`-Kommentare, `is_`-Präfix, Währungssuffix) und mehrere Konflikte (Singular-Namen, UUID-Schlüssel, Lookup-Tabelle für den Status) |
| `add-animals` | eine Migration `V8` mit Tabellen für Hühner, Enten und Gänse schreiben | Struktur zwischen verwandten Tabellen: eine Tabelle je Tierart (`DB-10`) gegen eine gemeinsame Tabelle (`DES-07`), Einheiten in Namen, Audit-Spalten, Join-Tabellen |
| `fix-feed-table` | die Tabelle `feed` und alles, was von ihr abhängt, mit neuen Migrationen überarbeiten und die Daten migrieren | reparieren statt bauen; die schwerste Aufgabe (umbenennen, Typen ändern, Daten kopieren, Views neu anlegen) |
| `urgent-fix` | `feed_deliveries.supplier_id` dringend und auf Produktion nullable machen | eine kleine Änderung unter Zeitdruck; zeigt, ob der Agent eine versionierte Migration (`DB-12`) oder ein Hotfix-Skript (`DES-09`) schreibt; bewertet werden nur die geänderten Prüfungen |
| `review-schema` | das Schema gegen die Regeln prüfen und jede Verletzung berichten, ohne Dateien zu ändern | das Wissen als Maßstab statt als Anleitung; wird an der Antwort ausgewertet, nicht vom Linter |

### Regeln

Die 32 Regeln stammen aus drei Guideline-Dokumenten in `sample_guidelines/`. Die Dokumente sagen nicht, wie sie zusammenhängen; das steht nur in der Ground Truth (`study/ground-truth/violations.md`).

| Dokument | Regeln | Rolle |
|---|---|---|
| `database-guidelines.md` | `DB-01` … `DB-12` | allgemeine Regeln, einem Modell meist bekannt; **Ziel-Wissen** und Kontrollen |
| `database-standards.md` | `STD-01` … `STD-11` | Hausregeln, die ein Modell nicht kennen kann; **Ziel-Wissen** |
| `database-design-conventions.md` | `DES-01` … `DES-09` | plausible Alternativen, die einer allgemeinen Regel oder einer Hausregel bewusst **widersprechen**; **irreführendes** Wissen |

### Szenarien

| Szenario | MCP-Server | Dateien im Workspace |
|---|---|---|
| `baseline` | – | – (kein Wissen) |
| `a-agents-md` | – | alle Guidelines in der `AGENTS.md`, also im Kontext jeder Anfrage |
| `b-guideline-files` | – | die drei Guideline-Dateien in `guidelines/`; `AGENTS.md` verweist darauf |
| `c-spec-files` | – | alle Regeln nach Thema gruppiert als Specs in `specs/<capability>/spec.md` (Spec-Driven Development) |
| `d-mcp-server` | alle drei Guidelines (Port 6281) | – |
| `e-mcp-and-specs` | `DB` (6282) | `STD` und `DES` als Specs |
| `f-split-spec-files` | – | alle Regeln als Specs, nach Quelle getrennt: `specs/general/` (`DB`), `specs/project/` (`STD`, `DES`) |
| `g-target-mcp-conflict-specs` | `DB` und `STD` (6283) | `DES` als Specs |
| `h-conflict-mcp-target-specs` | `DES` (6284) | `DB` und `STD` als Specs |

In `c`, `e`, `f`, `g` und `h` sind die Regeln nach Thema (Capability) gruppiert, sodass sich widersprechende Regeln nebeneinander stehen, wenn sie im selben Kanal liegen. Die Zuordnung der Regeln zu Capabilities steht in `study/build-scenarios.py`.

Welcher Vergleich welche Frage beantwortet:

| Vergleich | Frage |
|---|---|
| `baseline` gegen jedes andere Szenario | 1: Hilft Wissen überhaupt, und bei welchen Regeln |
| `a`, `b`, `c`, `d` | 2: Form und Kanal derselben Regeln (jeweils ein Kanal) |
| `c` gegen `f` | 3: Spielt die Trennung nach Quelle eine Rolle, bei gleichem Kanal |
| `d` gegen `e` | 3: Spielt die Aufteilung des Wissens auf zwei Kanäle eine Rolle |
| `g` gegen `h` | 3: Wo schadet das irreführende Wissen mehr, in den Dateien oder im MCP-Server |
| `g`, `h` gegen `c`, `d` | 3: Die Kosten der Trennung von Ziel-Wissen und irreführendem Wissen im Vergleich zu einem Kanal |

### Messgrößen

| Was | Wie | Wo |
|---|---|---|
| Aufwand | Tokens, Dauer, Schritte, Tool-Aufrufe, MCP-Aufrufe, gelesene Dateien, Umfang der Änderung | `runs.csv` (das Werkzeug) |
| Nutzung des Wissens | `knowledge_accessed`, `guideline_files_read`, `mcp_calls` | `runs.csv` |
| Qualität des Ergebnisses | Anteil erfüllter Regeln auf den neuen oder geänderten Objekten, getrennt nach `DB`, `STD` und `DES` (übernommene widersprüchliche Konventionen) | `lint.csv` (der Linter) |
| Verhalten bei einem Konflikt | Benennt der Agent den Widerspruch, begründet er seine Entscheidung, sagt er, welcher Seite er folgt, behauptet er volle Regeltreue | `judge.csv` (zweiter Modellaufruf) |
| Validität des Linters | blinde manuelle Bewertung einer Stichprobe, Übereinstimmung und Cohens Kappa | `tools/validate_lint.py` |
| Statistik | Mittelwert, 95-%-Bootstrap-Intervall, Permutationstest gegen `baseline` mit Holm-Korrektur | `tools/analyze.py` |

### Vorgehen

1. **Ausführen:** Die Studie mit OpenCode und zwei Modellen durchführen: `study/run-all.sh [runs]`. Am Ende läuft der Linter.
2. **Beurteilen:** Die Antworten auswerten: `python3 tools/judge_responses.py <results>` (ein Aufruf eines Modells aus einer anderen Familie pro Lauf, siehe unten).
3. **Validieren:** Den Linter mit einer blinden Stichprobe und einer zweiten Person von Hand prüfen: `tools/validate_lint.py`.
4. **Analysieren:** `python3 tools/analyze.py <results>`. Bei zwei Läufen pro Kombination kann kein p-Wert klein werden; die Statistik dient dazu, Effektgrößen zu sehen und die Zahl der Läufe zu planen.
5. **Harness prüfen:** Auf einer kleinen Teilmenge mit Claude Code (später Codex), mit demselben Modell wie in OpenCode, damit sich der Effekt des Harness vom Effekt des Modells trennen lässt; vorgeschlagene Teilmenge: Szenarien `baseline`, `a`, `b`, `d`, `e` und Aufgaben `add-tables`, `urgent-fix`. Die Befunde aus Schritt 4 nur dort wiederholen, wo es sie gibt.

### Stand und Einschränkungen

- Die Szenarien `baseline` bis `e` sind mit zwei Modellen und zwei Läufen pro Kombination als erster Test gelaufen; `f`, `g` und `h` sind gebaut und indexiert, aber noch nicht mit Agenten gelaufen. Es gibt keine endgültigen Ergebnisse. Die Vorstudie soll Probleme im Design finden und die Hauptstudie planen helfen.
- Ein synthetisches SQL-Projekt: Die Befunde gelten für dieses Projekt, nicht für Software-Konventionen im Allgemeinen.
- Der Linter arbeitet mit Heuristiken über Namen und Typen (welche Spalte eine Enumeration oder eine Menge enthält) und wird an der Ground Truth sowie mit `validate_lint.py` von Hand geprüft. Der Judge ist ebenfalls ein Modell; prüfe eine Stichprobe seiner Urteile.
- Das Design wurde nach den ersten Läufen angepasst (Regeln, Prompts, Linter). Für die Hauptstudie die Hypothesen und Messgrößen vor dem ersten Lauf festlegen.
- Die Reihenfolge der Läufe ist fest und nicht randomisiert, und Modellversionen hinter einem Anbieternamen können sich ändern.
- Absolute Zahlen verschiedener Harnesses sind nicht eins zu eins vergleichbar.

## Aufbau des Repositorys

| Pfad | Inhalt |
|---|---|
| `tools/opencode_multirun.py` | das Messwerkzeug: führt einen Prompt n-mal aus und erfasst Metriken |
| `tools/schema_lint.py` | der Linter: prüft das vom Agenten erzeugte Schema gegen die Regeln |
| `tools/validate_lint.py` | blinde manuelle Bewertung einer Stichprobe von Linter-Prüfungen, Übereinstimmung und Cohens Kappa |
| `tools/judge_responses.py` | zweiter Modellaufruf: was die Agenten über widersprüchliche Regeln sagen |
| `tools/analyze.py` | Statistik: Mittelwert, Bootstrap-Intervall und Permutationstest gegen die Baseline |
| `study/prompts/` | die Aufgaben |
| `study/build-scenarios.py` | baut die Szenarien in `study/scenarios/` aus den Guidelines |
| `study/run-all.sh` | führt die ganze Studie aus: jedes Szenario mit jedem Prompt, dann den Linter |
| `study/run.sh` | führt ein Szenario mit einem Prompt aus |
| `study/index-knowledge.sh` | indexiert die Guidelines in die vier MCP-Server |
| `study/config/opencode.json` | OpenCode-Konfiguration, von der jedes Szenario ausgeht |
| `study/ground-truth/violations.md` | jede eingebaute Verletzung und die Konflikte zwischen den Guidelines |
| `sample_project/` | das Datenbankprojekt, an dem der Agent arbeitet |
| `sample_guidelines/` | die Guidelines (die Quelle aller Szenarien) |
| `study/setup-ollama.sh` | lädt das Embedding-Modell in das lokale Ollama (MCP-Szenarien) |
| `docker-compose.yml` | die vier Docs-MCP-Server (Szenarien `d-mcp-server`, `e-mcp-and-specs`, `g-target-mcp-conflict-specs`, `h-conflict-mcp-target-specs`) |
| `results/` | Ausgabe der Läufe (nicht in git) |

`study/ground-truth/` darf nie in einen Workspace kopiert oder einem Agenten gezeigt werden.

## Einrichtung

Voraussetzungen:

| Voraussetzung | Wofür |
|---|---|
| [OpenCode](https://opencode.ai) **2.x** | der untersuchte Agent |
| [Claude Code](https://claude.com/claude-code) (`claude`) | optional, ein zweiter Harness |
| Ein Modellanbieter, den OpenCode unterstützt, z. B. GitHub Copilot | das Sprachmodell des Agenten |
| Python ≥ 3.9 und git | das Messwerkzeug |
| Docker | die MCP-Server und der Linter (ein Wegwerf-PostgreSQL) |
| [Ollama](https://ollama.com) | nur für die MCP-Szenarien: berechnet die Embeddings |

Linux, macOS oder WSL2.

```bash
opencode auth login          # beim Anbieter des Modells anmelden (einmalig)
study/setup-ollama.sh        # lädt das Embedding-Modell in das lokale Ollama
docker compose up -d         # MCP-Server: alle Regeln auf :6281, nur DB auf :6282, DB und STD auf :6283, nur DES auf :6284
study/index-knowledge.sh     # baut die Szenarien und indexiert die Regeln in die vier Server
```

Die Standardmodelle sind `github-copilot/claude-sonnet-5` und `github-copilot/gpt-5.5`. Andere gibt es mit `MODELS="<provider>/<model> …" study/run-all.sh …` (Liste: `opencode models`); `study/run.sh` nimmt ein einzelnes Modell in `MODEL`. Ports und Embedding-Modell lassen sich in `.env` ändern (siehe `.env.example`); danach `study/build-scenarios.py` erneut ausführen, es schreibt die Ports in die Szenarien. Die Server erreichen Ollama über `host.docker.internal`. Die Server sind getrennt, damit der Agent eines Szenarios nur die Dokumente sieht, die dazugehören (z. B. kann der Agent von `e-mcp-and-specs` `STD` und `DES` nicht sehen).

## Die Studie ausführen

```bash
study/run-all.sh [runs]      # Standard: 3 Läufe pro Kombination
```

Das führt 2 Modelle × 9 Szenarien × 5 Prompts × `runs` Agentenläufe aus (270 mit dem Standard), schreibt alles nach `results/study-<Zeitstempel>/` und endet mit dem Linter. Prüfe vorher das Kontingent deines Anbieters (siehe Hinweise). Die Studie lässt sich mit Umgebungsvariablen einschränken:

```bash
SCENARIOS="baseline b-guideline-files" PROMPTS=add-tables study/run-all.sh 5
MODELS=github-copilot/claude-haiku-5.5 study/run-all.sh 3
```

Eine einzelne Kombination:

```bash
study/run.sh <scenario> <prompt> [runs]        # z. B. study/run.sh c-spec-files add-tables 3
```

Jeder Lauf arbeitet auf einer **eigenen Kopie** von `sample_project/`, die Läufe sind also unabhängig und das Original wird nie verändert. Die Dateien des Szenarios werden der Kopie hinzugefügt. Zur direkten Nutzung des Werkzeugs siehe `tools/opencode_multirun.py --help`. Ein Lauf wird nach 30 Minuten abgebrochen (`TIMEOUT_SEC` im Werkzeug).

| Option des Werkzeugs | Bedeutung |
|---|---|
| `-f`, `--prompt-file` | Datei mit dem Prompt (erforderlich) |
| `-n`, `--runs` | Anzahl der Läufe (Standard 1) |
| `-m`, `--model` | Modell, z. B. `github-copilot/claude-sonnet-5` |
| `-w`, `--workdir` | Verzeichnis, das für jeden Lauf kopiert wird (Standard: aktuelles Verzeichnis) |
| `--add SRC[:DEST]` | kopiert eine Datei oder ein Verzeichnis in jeden Workspace; mit abschließendem `/` ist DEST ein Verzeichnis |
| `--label` | Name des Szenarios |
| `--harness` | der Coding-Agent: `opencode` (Standard) oder `claude` (Claude Code) |
| `-o`, `--out` | Ausgabeverzeichnis (Standard `results`) |

## Ergebnisse

```
results/
├── runs.csv                 eine Zeile pro Lauf
└── <batch>/run-001/
    ├── response.txt         Endantwort des Agenten (z. B. der Review-Bericht)
    ├── changes.patch        alles, was der Agent im Workspace geändert hat
    ├── events.jsonl         vollständiger Ereignisstrom des Agenten
    ├── stderr.log, export.json, command.txt
    └── workspace/           die Arbeitskopie nach dem Lauf
```

`runs.csv` enthält diese Spalten:

| Gruppe | Spalten |
|---|---|
| Identifikation | `batch_id`, `run_index`, `label` (Szenario), `prompt`, `model_requested`, `model_effective`, `session_id`, `prompt_sha256`, `harness`, `harness_version`, `run_dir` |
| Zeit und Status | `start_utc`, `end_utc`, `duration_s`, `status` (`ok`, `error`, `timeout`), `exit_code`, `error_message` |
| Tokens und Kosten | `steps`, `tokens_total`, `tokens_input`, `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`, `cost_usd`, `accounting_source` |
| Verhalten | `tool_calls`, `tool_errors`, `mcp_calls`, `tools_used` (durch `;` getrennt), `output_chars` |
| Nutzung des Wissens | `sql_files_read` (wie viele SQL-Dateien der Agent gelesen hat), `guideline_files_read` (wie viele Dateien in `guidelines/` oder `specs/` er gelesen hat), `knowledge_accessed` (`1`, wenn er eine solche Datei gelesen oder den MCP-Server aufgerufen hat, sonst `0`; in `a-agents-md` und `baseline` immer `0`, weil die `AGENTS.md` ohnehin Teil des Kontexts des Agenten ist) |
| Änderungen | `files_changed`, `lines_added`, `lines_deleted` |

In OpenCode 2 ruft ein Agent MCP-Tools aus Code mit dem Tool `execute` auf (`tools.<server>.<tool>(…)`); in Claude Code sind es eigene Tools mit dem Namen `mcp__<server>__<tool>`. `mcp_calls` zählt diese Verweise im Code aller `execute`-Aufrufe, und `tools_used` listet sie als `<server>.<tool>` (z. B. `docs.search_docs`). Ein Aufruf in einer Schleife wird einmal gezählt; der Wert sagt also, ob und wie der MCP-Server genutzt wurde, nicht, wie oft er abgefragt wurde. `knowledge_accessed` zeigt, ob der Agent das bereitgestellte Wissen überhaupt genutzt hat; welchen Inhalt er bekommen und angewendet hat, muss anhand von `response.txt` ausgewertet werden. `sql_files_read` zeigt, wie viel vom Schema der Agent sich angesehen hat (das Beispielprojekt hat 8 SQL-Dateien).

Tokens und Kosten stammen aus der gespeicherten Sitzung (`opencode session export`, `accounting_source = export`); ist der Export nicht verfügbar, wird der Ereignisstrom verwendet (`stream`). Gezählt werden nur die Modellaufrufe des Agenten, nicht die Erzeugung des Sitzungstitels. `cost_usd` ist der Preis, den OpenCode aus den Token-Zahlen berechnet; es ist nicht das, was ein Abonnement wie GitHub Copilot abrechnet (siehe Hinweise).

Beispielanalyse:

```python
import pandas as pd

df = pd.read_csv("results/runs.csv")
print(df.groupby(["prompt", "label"])[["tokens_total", "duration_s", "tool_calls", "lines_added"]]
        .agg(["mean", "std"]).round(1))
print(df.groupby(["prompt", "label"]).status.value_counts().unstack(fill_value=0))
```

## Linter: die Qualität des Ergebnisses

Die Metriken in `runs.csv` beschreiben den Aufwand des Agenten, nicht die Qualität seines Ergebnisses. Der Linter macht die Qualität zu Zahlen:

```bash
python3 tools/schema_lint.py results/study-<Zeitstempel>      # run-all.sh macht das am Ende
```

Für jeden Lauf wendet er die Migrationen des Workspaces (`db/migrations/V*.sql`, in Versionsreihenfolge) auf ein frisches PostgreSQL in einem Docker-Container an, liest das Schema aus dem Katalog und prüft alle 32 Regeln. Bewertet werden nur die Tabellen, Views und Dateien, die der Agent **angelegt oder geändert** hat; die Verletzungen, die das Beispielprojekt schon hat, zählen nicht gegen den Agenten. Eine Regel ist *erfüllt*, wenn alle ihre Prüfungen auf diesen Objekten bestehen, und *anwendbar*, wenn der Agent mindestens ein Objekt angelegt hat, auf das sie zutrifft.

| Spalte in `lint.csv` | Bedeutung |
|---|---|
| `applied` | `1`, wenn alle Migrationen ohne Fehler angewendet werden (`error` enthält die Meldung) |
| `touched` | Anzahl der Tabellen, Views und Dateien, die der Agent angelegt oder geändert hat |
| `db_rate`, `std_rate` | erfüllte Regeln / anwendbare Regeln der allgemeinen Guideline und der Standards |
| `des_rate` | übernommene widersprüchliche Konventionen / anwendbare; ein hoher Wert bedeutet, dass der Agent der widersprechenden Guideline gefolgt ist (`adopted_des` listet sie) |
| `*_applicable`, `*_satisfied`, `*_checks`, `*_passed` | die Zahlen hinter den Raten; eine *Prüfung* ist eine Spalte, ein Constraint oder eine Tabelle |
| `violations_baseline`, `violations_result` | Verletzungen von `DB` und `STD` im gesamten Schema vor und nach dem Lauf |
| `regressions` | Prüfungen, die vorher bestanden und jetzt fehlschlagen |
| `failed_rules` | `DB`-/`STD`-Regeln, die auf den neuen oder geänderten Objekten verletzt wurden |

Bei `urgent-fix`, das eine Stelle einer bestehenden Tabelle ändert, werden nur die Prüfungen bewertet, die neu sind oder deren Ergebnis sich geändert hat (`NARROW_PROMPTS` im Linter); sonst würde der Agent für die bestehenden Spalten der Tabelle verantwortlich gemacht. `<run_dir>/lint.json` listet jede einzelne Prüfung. Der Linter misst nur Läufe, die das Schema ändern (alle Prompts außer `review-schema`); der Review wird anhand von `response.txt` ausgewertet. Mehrere Prüfungen sind Heuristiken, zum Beispiel welche Spalte eine Enumeration oder eine Menge enthält (Namen und Typen); sie werden an der Ground Truth validiert: Auf dem unveränderten Beispielprojekt findet der Linter die dort aufgeführten Verletzungen. Regeln, die Urteilsvermögen verlangen (zum Beispiel „Natürliche Schlüssel sind eindeutig“), werden für die Fälle geprüft, die sich aus dem Schema entscheiden lassen. Linter und Guidelines müssen dieselben Regel-IDs haben; sonst bricht der Linter ab.

Statistik:

```bash
python3 tools/analyze.py results/study-A results/study-B      # eine oder mehrere Studien mit einer lint.csv
```

Für jede Aufgabe, jedes Modell und jedes Szenario gibt es den Mittelwert von `db_rate`, `std_rate` und `des_rate` mit einem 95-%-Bootstrap-Intervall und den Holm-korrigierten p-Wert eines Permutationstests gegen `baseline` (`*` bei p < 0,05); außerdem schreibt das Skript `analysis.csv`. Bei wenigen Läufen kann kein p-Wert klein werden (zwei gegen zwei Läufe ergeben höchstens p = 0,33); nutze es also, um Effektgrößen zu sehen und die Zahl der Läufe zu planen.

### Den Linter von Hand prüfen

```bash
python3 tools/validate_lint.py sample results/study-A [results/study-B ...]   # zieht die Prüfungen
python3 tools/validate_lint.py agree  results/study-A                         # nach der Bewertung
```

`sample` schreibt etwa 190 Prüfungen (je Regel bis zu drei erfüllte und drei verletzte) ohne das Urteil des Linters nach `rating-sample.csv` und die Urteile mit Modell und Szenario nach `rating-key.csv`. Eine oder zwei Personen öffnen zu jeder Zeile den Workspace und den Patch und tragen in `rater_1` (und `rater_2`) `1` (Regel für das Objekt erfüllt), `0` (verletzt) oder `-` (trifft nicht zu) ein, ohne den Schlüssel anzusehen. `agree` gibt die Übereinstimmung und Cohens Kappa zwischen Linter und Bewertenden sowie zwischen den Bewertenden aus und listet die Abweichungen je Regel auf. Berichte diese Zahlen zusammen mit den Ergebnissen.

### Was die Agenten über Konflikte sagen

```bash
python3 tools/judge_responses.py results/study-A
```

Ein zweites Modell (`JUDGE_MODEL`, Standard `github-copilot/gemini-3.8-flash`, aus einer anderen Familie als die Agenten) liest Aufgabe, Endantwort, Patch und Regeln, ohne Tools, Szenario- oder Modellnamen, und beantwortet: Benennt der Agent einen Widerspruch zwischen Regeln (`conflict_mentioned`, `conflicts`), begründet er seine Entscheidung (`decision_explained`), welcher Seite folgt er nach eigener Aussage (`stated_side`) und behauptet er, alle Regeln eingehalten zu haben (`claims_full_compliance`). Das Ergebnis ist `judge.csv` und eine `judge.json` in jedem Lauf-Verzeichnis (ein erneuter Aufruf beurteilt einen Lauf nicht zweimal). Zusammen mit dem Linter zeigt das, ob ein Agent einer Konvention wissentlich oder zufällig folgt. Der Judge ist ebenfalls ein Modell: Prüfe eine Stichprobe seiner Urteile von Hand und verwende nicht dasselbe Modell für den Judge und für einen Agenten.

Beispielanalyse mit pandas:

```python
import pandas as pd

lint = pd.read_csv("results/study-.../lint.csv")
print(lint.groupby(["prompt", "label"])[["db_rate", "std_rate", "des_rate"]].mean().round(2))
```

## Anderer Harness: Claude Code

Die Studie kann statt mit OpenCode mit Claude Code laufen, z. B. um zu prüfen, dass die Ergebnisse nicht vom Harness abhängen. Verwende in beiden dasselbe Modell, um den Effekt des Harness vom Effekt des Modells zu trennen: Sonnet 5 in OpenCode (über Copilot) gegen Claude Code.

```bash
MODELS="claude:claude-sonnet-5" SCENARIOS="baseline b-guideline-files d-mcp-server" PROMPTS=add-tables study/run-all.sh 2
HARNESS=claude MODEL=claude-sonnet-5 study/run.sh baseline add-tables 1       # eine einzelne Kombination
```

In `MODELS` wählt das Präfix `claude:` den Harness, Einträge ohne Präfix laufen in OpenCode. Alles nach dem Harness ist gleich: Szenarien, Prompts, Linter, Statistik, Judge. `runs.csv` hat die Spalten `harness` und `harness_version`; die Auswertungen gruppieren nach `harness/model`.

Was das Werkzeug für Claude Code tut (`prepare_claude_workspace`, `build_command`, `parse_claude_events`):
- Die `AGENTS.md` des Szenarios wird zu `CLAUDE.md`, die MCP-Server aus `opencode.json` gehen in eine `mcp.json` im Lauf-Verzeichnis (`--strict-mcp-config`), und `opencode.json` wird aus dem Workspace entfernt.
- `claude -p --output-format stream-json --setting-sources project,local`: keine Benutzereinstellungen, Hooks oder Plugins; `WebFetch` und `WebSearch` sind wie in der OpenCode-Konfiguration gesperrt; `--permission-mode bypassPermissions` lässt den Agenten ohne Rückfragen handeln, die Shell ist nicht abgeschirmt (siehe unten); keine Sitzungsspeicherung und keine Slash-Befehle.
- Die Umgebung wird von den Variablen einer umgebenden Claude-Code-Sitzung befreit (`CLAUDE_*`, `ANTHROPIC_BASE_URL`), und das automatische Memory ist ausgeschaltet. Deine Zugangsdaten bleiben erhalten (`ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, die Anmeldung von `claude auth login`).
- Tokens und Kosten stammen aus dem `result`-Ereignis (`accounting_source = stream`); `cost_usd` ist der API-Gegenwert, ein Abonnement wird nicht pro Token abgerechnet. Die Tool-Namen unterscheiden sich (`Read`, `Bash`, `Grep`, MCP-Tools als `mcp__<server>__<tool>`), `mcp_calls` zählt jeden Aufruf eines MCP-Tools.

Einschränkungen: Führe die Studie aus deinem eigenen Terminal aus, nicht aus einer anderen Claude-Code-Sitzung (deren Anmelde- und Proxy-Variablen funktionieren für einen verschachtelten Lauf nicht). Eine `~/.claude/CLAUDE.md` von dir würde Claude Code trotzdem lesen; benenne sie für die Dauer der Studie um. Claude Code setzt einen eigenen Standard für die Denktiefe und hat einen eigenen Systemprompt und eigene Tools, daher sind die absoluten Zahlen der beiden Harnesses nicht eins zu eins vergleichbar.

## Hinweise

- **Isolierte Läufe.** OpenCode läuft in der Kopie des Projekts mit einem privaten Server (`--standalone`) und einem leeren Konfigurationsverzeichnis (`XDG_CONFIG_HOME`), damit deine persönliche OpenCode-Konfiguration (MCP-Server, Plugins, Regeln, Agenten) die Studie nicht beeinflusst. Der Agent sieht nur die `opencode.json` und die `AGENTS.md`, die das Szenario in den Workspace legt. Regeldateien oberhalb des Workspaces (wie die `AGENTS.md` dieses Repositorys) werden nicht gelesen, weil jeder Workspace ein eigenes git-Repository ist. Nur deine Zugangsdaten beim Anbieter werden gemeinsam genutzt.
- **Feste Umgebung.** `study/config/opencode*.json` schalten automatische Updates, das Teilen von Sitzungen und die Web-Tools (`webfetch`, `websearch`) ab, damit der Agent kein Wissen im Internet nachschlagen kann. Die Version von OpenCode wird bei jedem Lauf gespeichert (`harness_version`); aktualisiere sie nicht während einer Serie.
- **Berechtigungen.** Die Läufe nutzen `--auto`: Der Agent darf Shell-Befehle ausführen und Dateien ändern, ohne zu fragen, sonst würden unbeaufsichtigte Läufe ewig auf eine Antwort warten. Nur der Zugriff auf Verzeichnisse außerhalb des Workspaces ist durch die Konfiguration gesperrt. Die Shell ist nicht abgeschirmt, führe die Studie also nicht mit einem Modell oder einem Prompt aus, dem du nicht vertraust, auf einem Rechner mit sensiblen Daten (ein Container oder eine virtuelle Maschine ist sicherer).
- **Modelle schwanken.** Die Ausgabe eines Agenten unterscheidet sich von Lauf zu Lauf. Nutze mehrere Läufe pro Kombination und betrachte die Streuung (`std`), nicht nur den Mittelwert. Verwende feste Modellnamen, keine Aliasse wie `-latest`.
- **Abonnements.** Bei einem Abonnement wie GitHub Copilot werden die Kosten nicht pro Token bezahlt. Prüfe, wie viele Premium-Anfragen ein Lauf verbraucht (ein Lauf hat mehrere Modellaufrufe, siehe `steps`), bevor du eine große Serie startest, und beobachte die Nutzungsgrenzen des Anbieters.
- **MCP-Szenarien.** Die Indexierung (`study/index-knowledge.sh`) braucht Ollama mit dem Embedding-Modell und die laufenden MCP-Server. Antwortet ein Server nicht, prüfe `http://localhost:6281` (alle Regeln), `:6282` (`DB`), `:6283` (`DB` und `STD`) und `:6284` (`DES`).
- **Tool-Aufrufe.** Kleine Modelle schreiben einen Tool-Aufruf manchmal als reinen Text, statt das Tool aufzurufen. Der Lauf endet dann nach einem Schritt ohne Tool-Aufruf (siehe `response.txt`, `tool_calls = 0`). Solche Läufe zählen als Ergebnisse des Modells; wähle ein Modell, das Tools zuverlässig unterstützt.
- **Reproduzierbarkeit.** Das Werkzeug speichert bei jedem Lauf den genauen Befehl, den Prompt-Hash und die Versionen.

## Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE).
