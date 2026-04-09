# Capstone TestTribe QA Automation : Option 4 — AC Completeness Auditor

A modular Python agent pipeline for QA operations: Jira story fulfillment, test case generation, TestRail upload, and acceptance criteria completeness auditing with Slack reporting.

## Project structure

- `src/graph/drivers/run_ac_audit.py` - new pipeline for Jira AC completeness audit and Slack report.
- `src/graph/jira_ac_audit/...` - new multi-agent graph and agents for AC audit.
- `src/integrations/jira_client.py` - Jira read-only API integration with issue fetch/search.
- `src/integrations/slack_client.py` - Slack posting utility.
- `data/knowledge_base/` - markdown documents used for RAG context (`testing_guidelines.md`, etc.).

## Setup

1. Create and activate virtual env

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install requirements

```powershell
pip install -r requirements.txt
```

3. Configure `.env` at project root:

```ini
# Jira
JIRA_BASE_URL=http://localhost:4001
JIRA_TOKEN=<your-jira-token>

# Jira fallback by key list (quotes are allowed)
JIRA_STORY_KEYS="QA-1,QA-2,QA-3"

# Slack
SLACK_BASE_URL=http://localhost:4003
SLACK_TOKEN=<your-slack-token>
SLACK_CHANNEL=qa-reports

# OpenAI
PROVIDER=openai
MODEL=gpt-4o-mini
OPENAI_API_KEY=<your-openai-key>

# Optional fallback for environments without langchain_chroma
SEARCH_VECTOR_STORE_FALLBACK=1
```

### Why `JIRA_STORY_KEYS` matters

- If Jira `/rest/api/3/search` returns `422` (common for lightweight/mock Jira servers), the pipeline will still work when `JIRA_STORY_KEYS` is set.
- The audit agent first resolves the key list, strips optional quotes, and fetches each issue individually.
- No `/search` call is made when `JIRA_STORY_KEYS` is present.


4. Build vector store (if applicable)

```powershell
python -c "from src.core.vectore_store import build_vector_store; build_vector_store()"
```

## Run pipelines

### AC audit + suggestions -> Slack

- All stories (requires Jira search support or environment keys):

```powershell
python -m src.graph.drivers.run_ac_audit all
python -m src.graph.drivers.run_tc_qualityReviewer
```

- Single story

```powershell
python -m src.graph.drivers.run_ac_audit QA-1
```

- Streamlit:

### Streamlit UI

To launch the Streamlit UI:

```powershell
streamlit run app.py
# or, if you want to be explicit about the venv:
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**Note:** By default, the UI will show "No pipelines available yet" until you uncomment and configure at least one pipeline in `src/ui/pipeline_registry.py`.

### Troubleshooting: torchvision errors

If you see errors like `ModuleNotFoundError: No module named 'torchvision'` or repeated background logs from `transformers` about missing vision dependencies, install torchvision in your virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Then verify:
```powershell
python -c "from torchvision.io import read_image; print('ok')"
```

Restart Streamlit after installing.


Output files:

- `outputs/jira_ac_audit/<jira_key>_ac_audit_report.txt`

## Key features

- `jira_fetcher` for story fetching (read-only, no update/write back).
- AC parser extracts structured acceptance criteria from story description.
- AC completeness scorer with directed categories (happy path, error, boundary, UI, security, persistence) and score out of 10.
- Gap identifier for missing AC types and actionable improvement suggestion generation (Given/When/Then).
- Slack reporter posts a per-story audit to configured Slack channel.
- History caching in `data/audit_history.json` to skip unchanged story scans.

## Notes

- If your Jira service does not support `/rest/api/3/search`, set `JIRA_STORY_KEYS` in `.env` and run with `all`.
- If Chroma is unavailable, set `SEARCH_VECTOR_STORE_FALLBACK=1` to use lightweight local KB lookup fallback.
- Keep `data/knowledge_base/` updated to improve RAG prompt recommendations.
