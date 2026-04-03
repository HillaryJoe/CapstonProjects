# Capstone Project — Agentic AI for QA

## What This Capstone Proves

Over the last 4 weeks you learned how to build AI agents from scratch — from basic LLM calls to full multi-agent pipelines with real integrations. Today you apply everything in one cohesive project.

By the end of this session you will have built a working QA agent that:
- Orchestrates multiple specialist agents using LangGraph and the supervisor pattern
- Uses RAG to make decisions grounded in QA knowledge standards
- Persists state across runs using Memory
- Reads from and writes to real tools — Jira, TestRail, and Slack
- Runs end-to-end and produces a result you can demo live

Pick ONE project from the four options below. Work as a team. One person codes, everyone contributes.

---

## Pre-requisites & Setup

Complete these steps before you start building.

### Step 1 — Copy the Knowledge Base Documents

The RAG knowledge base needs domain-specific documents for your agent to reason against. Four new documents have been prepared for you.

Copy all files from:
```
assignments/capstone/knowledge_base/
```

Into:
```
data/knowledge_base/
```

The four new documents are:
- `sprint_qa_checklist.md` — sprint coverage thresholds and exit criteria
- `test_case_quality_standards.md` — completeness scoring and anti-patterns
- `regression_testing_guide.md` — mapping bugs to regression tests
- `acceptance_criteria_standards.md` — AC completeness and testability standards

---

### Step 2 — Rebuild the RAG Index

The vector store at `data/vector_store/` was built during Day 5 from the original 3 knowledge base documents. Now that you have added 4 new documents, the index must be rebuilt so your agent can search across all 7 documents.

**Choose one option based on whether you have an OpenAI API key:**

#### Option A — Using OpenAI (same as Day 5, no code changes needed)

If you already have a working `OPENAI_API_KEY` in your `.env`, just run:

```bash
python build_index.py
```

That is it. The index rebuilds with all 7 documents using OpenAI embeddings.

#### Option B — Using HuggingFace (free, no API key required)

If you do not have an OpenAI API key, you need to make a small code change to `src/core/vectore_store.py` to use a free local model instead.

Follow the step-by-step instructions in:
```
assignments/capstone/huggingface_embedding_setup.md
```

That guide shows exactly which lines to change, what to replace them with, and how to rebuild the index. The `sentence-transformers` package is already installed — no new installs needed.

> **Important:** You cannot mix embedding models. If you built the index with OpenAI, use OpenAI to query it. If you switch to HuggingFace, rebuild the index first.

---

### Step 3 — Verify the Mock Services Are Running

Start the mock services if they are not already running:
```bash
cd /path/to/Jira_Testrail_Slack_Demo_Service
./start-all.sh
```

| Service   | UI                          | API                        |
|-----------|-----------------------------|----------------------------|
| Jira      | http://localhost:4001/ui    | http://localhost:4001/docs |
| TestRail  | http://localhost:4002/ui    | http://localhost:4002/docs |
| Slack     | http://localhost:4003/ui    | http://localhost:4003/docs |

The Jira mock is pre-seeded with 7 issues (QA-1 to QA-7). TestRail has 3 seed test cases.

---

## Mandatory Tech Stack

Every project must use all of the following. These are not optional:

| Topic        | What to Use                                               | Reference File                              |
|--------------|-----------------------------------------------------------|---------------------------------------------|
| LangGraph    | StateGraph with nodes, edges, and conditional routing     | `src/graph/jira_testrail_slack/graph.py`    |
| Multi-Agent  | Supervisor pattern — router node + specialist agent nodes | `src/graph/jira_testrail_slack/supervisor.py` |
| RAG          | Query the rebuilt vector store in at least one node       | `src/core/vectore_store.py`                 |
| Memory       | Persist state across runs using the memory layer          | `src/core/memory.py`                        |
| Integration  | At least one service with both a read and a write call    | `src/integrations/`                         |
| Slack        | Post a final summary message to #qa-reports channel       | `src/integrations/slack_client.py`          |

Streamlit UI is optional — building it is an added advantage and earns bonus points in the demo.

---

## Project Options

Pick ONE. Every option covers all mandatory topics.

---

### Option 1 — Sprint Coverage Gap Checker

**The Problem**

QA teams often discover at sprint review — or worse, after a release — that certain stories were shipped without a single test case. By then it is too late. This agent detects coverage gaps early and fills them automatically.

**What This Agent Does & Why**

This agent acts as an automated sprint QA gate. At any point during a sprint, a team lead can trigger it and immediately know the state of test coverage across all stories. The agent fetches every story from Jira, then independently fetches all test cases from TestRail, and performs a mapping to determine which stories have at least one test and which have none. For every uncovered story, it uses the LLM — guided by RAG over your sprint QA standards — to generate appropriate test cases and push them directly into TestRail. It then posts a coverage dashboard to the Slack #qa-reports channel with a Go / Caution / Block recommendation so the team can act before the sprint ends.

Without this agent, QA coverage checking is a manual, error-prone process. With it, a sprint can be audited in seconds and gaps are filled automatically rather than discovered too late.

**Input**

- All Jira stories in the system (QA-1, QA-2, QA-3, QA-7 are Stories — agent must filter by issue type)
- All existing test cases fetched from TestRail

**Expected Output**

- New test cases created in TestRail for every story that has zero test coverage
- A Slack message posted to `#qa-reports` containing:
  - Total stories analysed
  - Number of stories covered vs uncovered
  - Coverage percentage (e.g. 75%)
  - Go / Caution / Block recommendation based on thresholds
  - List of stories that had test cases generated

**Recommended Agent Nodes**

```
jira_stories_fetcher → testrail_cases_fetcher → coverage_analyzer →
testcase_generator → testrail_pusher → slack_reporter
```

**What Each Node Should Do**

- `jira_stories_fetcher` — Call the Jira search API, filter results by `issuetype = Story`, return a list of story keys, summaries, and descriptions. Store in state.
- `testrail_cases_fetcher` — Call the TestRail get_cases API, return all existing test case titles and IDs. Store in state.
- `coverage_analyzer` — For each story, check if any TestRail case title contains the story key or closely matches the story summary. Mark each story as covered or uncovered. Calculate the coverage percentage.
- `testcase_generator` — For each uncovered story, call the LLM with a prompt that includes the story description. Query RAG for sprint coverage standards before generating. Produce 2–3 structured test cases per uncovered story.
- `testrail_pusher` — For each generated test case, call the TestRail add_case API to push it into the test suite.
- `slack_reporter` — Format a clean summary message and post it to the `#qa-reports` channel using the Slack client.

**RAG Knowledge Base**
- `testing_guidelines.md`
- `sprint_qa_checklist.md`

**Integrations**
- Jira: read all stories
- TestRail: read existing cases + write new cases for gaps
- Slack: post coverage report

**Must-Have Requirements**

1. Agent uses the supervisor pattern — a router node decides which specialist runs next
2. Coverage analyzer maps stories to test cases before generating anything
3. RAG is queried before generating test cases to ensure they meet sprint standards
4. Memory records which stories were already processed — re-runs do not regenerate test cases for already-covered stories
5. Slack message clearly shows the coverage percentage and recommendation

**Stretch Goal — Streamlit UI**

A page where the trainer can trigger the agent and watch the coverage result populate live, showing a list of covered and uncovered stories with the generated test case titles.

---

### Option 2 — Test Case Quality Reviewer

**The Problem**

Test cases written quickly during sprints accumulate technical debt — vague steps, missing expected results, duplicate scenarios. Over time the test suite becomes unreliable and hard to maintain. This agent audits the suite and improves it automatically.

**What This Agent Does & Why**

This agent is a quality control system for your test suite. It reads every test case from TestRail, evaluates each one against a scoring rubric, identifies what is wrong, and then rewrites the weak ones directly in TestRail. It works in multiple passes: first it scores every test case for completeness (title quality, step specificity, expected result clarity), then it checks for near-duplicate cases, and finally it uses the LLM — guided by RAG over your test case quality standards — to rewrite any case that scores below the threshold. Only genuinely low-quality cases are touched; high-scoring ones are left as-is. A Slack report summarises what was found and fixed so the team has visibility without having to check TestRail manually.

This agent solves a real problem that every QA team faces: test suites that grow over time but are never maintained. Running it periodically ensures your test suite stays trustworthy and executable.

**Input**

- All existing test cases fetched from TestRail (the seed data has 3 cases; add more via the TestRail UI at http://localhost:4002/ui before running to make the demo richer)

**Expected Output**

- TestRail test cases updated in-place with improved titles, steps, and expected results where quality is below standard
- A Slack message posted to `#qa-reports` containing:
  - Total test cases reviewed
  - Number improved, number flagged as duplicates, number already high quality
  - Average quality score across all cases (out of 10)
  - Summary of the most common quality issues found

**Recommended Agent Nodes**

```
testrail_fetcher → completeness_checker → duplicate_detector →
improvement_suggester → testrail_updater → slack_reporter
```

**What Each Node Should Do**

- `testrail_fetcher` — Call the TestRail get_cases API and return all existing test cases with their full content (title, steps, expected results). Store in state.
- `completeness_checker` — For each test case, query RAG for the quality scoring rubric. Ask the LLM to score the test case out of 10 and identify which specific fields are missing or vague. Store scores and issues in state.
- `duplicate_detector` — Compare test case titles and steps across the full list. Flag pairs that appear to test the same scenario. Mark lower-scoring duplicates for removal or merge.
- `improvement_suggester` — For every test case scoring below 7, ask the LLM to rewrite it with specific steps, clear expected results, and proper preconditions. Use RAG context to ensure the rewrite meets quality standards.
- `testrail_updater` — For each improved test case, call the TestRail update_case API to replace the original content with the improved version.
- `slack_reporter` — Post a quality review summary to `#qa-reports`: total reviewed, number improved, average score before and after, most common issue type found.

**RAG Knowledge Base**
- `testing_guidelines.md`
- `test_case_quality_standards.md`

**Integrations**
- TestRail: read all cases + update improved cases
- Slack: post quality review summary

**Must-Have Requirements**

1. Agent uses the supervisor pattern
2. RAG is used to score each test case against the quality rubric (completeness score out of 10)
3. Only test cases scoring below 7 are updated — high quality cases are left unchanged
4. Memory stores the review results so re-runs can detect whether quality has improved over time
5. TestRail cases are actually updated via the API — not just reported

**Stretch Goal — Streamlit UI**

A page showing each test case with its before/after quality score, what was changed, and a summary bar chart of quality distribution.

---

### Option 3 — Bug-to-Regression Test Mapper

**The Problem**

When a bug is fixed, the code change is merged but no regression test is written. The same bug silently reappears in a future release. This agent closes that gap by automatically generating a regression test for every bug that does not yet have one.

**What This Agent Does & Why**

This agent bridges the gap between bug tracking and test coverage. It fetches every bug from Jira, then for each one it checks TestRail to see if a regression test already exists — if it does, the bug is skipped to avoid duplicates. For bugs with no regression coverage, the agent uses the bug's description, steps to reproduce, and expected vs actual behavior to generate a targeted regression test using the LLM, guided by RAG over your regression testing standards. The generated test follows a strict naming convention that ties it back to the original Jira bug key. It is then pushed directly into TestRail and the full regression coverage summary is posted to Slack.

The reason this agent matters: in most teams, regression tests are only written when someone remembers to do it. This agent makes it automatic — every bug that lands in Jira automatically gets a regression test without any manual effort.

**Input**

- All Jira bugs fetched from Jira (QA-4: Critical — login issue, QA-5: High — forgot password, QA-6: Medium — search bug — all pre-seeded as Bug type in the mock)

**Expected Output**

- Regression test cases created in TestRail for every bug that does not already have coverage, named using the convention: `REG — [BUG_KEY] — [scenario]`
- A Slack message posted to `#qa-reports` containing:
  - Total bugs analysed
  - How many already had regression tests (skipped)
  - How many new regression tests were created and which bug keys they cover
  - A coverage statement: "X of Y bugs now have regression coverage"

**Recommended Agent Nodes**

```
jira_bug_fetcher → regression_checker → regression_test_generator →
testrail_pusher → slack_reporter
```

**What Each Node Should Do**

- `jira_bug_fetcher` — Call the Jira search API with a filter for `issuetype = Bug`. Return each bug's key, summary, description, steps to reproduce, expected behavior, actual behavior, and priority. Store in state.
- `regression_checker` — For each bug, call the TestRail get_cases API and search existing case titles for the bug key (e.g. "QA-4"). If found, mark the bug as already covered and skip. If not found, mark it as needing a regression test.
- `regression_test_generator` — For each uncovered bug, query RAG for regression test writing standards. Then ask the LLM to generate a regression test using the bug's exact steps to reproduce as test steps and the expected behavior as the expected result. Title must follow: `REG — [BUG_KEY] — [short scenario description]`.
- `testrail_pusher` — Push each generated regression test to TestRail using the add_case API. Store the returned case IDs in state.
- `slack_reporter` — Post a regression coverage summary to `#qa-reports` listing which bugs now have coverage, which were skipped (already covered), and the overall coverage count.

**RAG Knowledge Base**
- `troubleshooting_guide.md`
- `regression_testing_guide.md`

**Integrations**
- Jira: read all bugs (filter by issuetype = Bug)
- TestRail: read existing cases to check for existing coverage + write new regression tests
- Slack: post regression coverage summary

**Must-Have Requirements**

1. Agent uses the supervisor pattern
2. The agent checks TestRail FIRST before generating — never create a duplicate regression test for a bug that is already covered
3. RAG is used when generating regression tests to ensure they follow the naming convention and quality standards
4. Memory tracks which bugs have been processed in previous runs — re-runs skip already-covered bugs
5. Each generated regression test title must include the original Jira bug key

**Stretch Goal — Streamlit UI**

A page showing each bug alongside its regression test status (covered / newly created / skipped) with a link to the TestRail case ID.

---

### Option 4 — AC Completeness Auditor

**The Problem**

Acceptance criteria written by PMs are often incomplete — they cover only the happy path, miss error scenarios, skip boundary conditions. QA teams discover the gaps only after test cases are written or, worse, after a defect escapes to production. This agent audits ACs before sprint work begins and posts actionable improvement suggestions.

**What This Agent Does & Why**

This agent acts as a QA consultant reviewing stories before the sprint even begins. It fetches all Jira stories, reads the acceptance criteria from each story's description, and then evaluates how complete those ACs are using a structured scoring rubric — powered by RAG over your AC standards document. It checks whether each story covers happy paths, error scenarios, boundary conditions, UI feedback, and security cases. For every gap it finds, it does not just say "add more edge cases" — it generates specific ready-to-use ACs written in Given/When/Then format that the PM can paste directly into the story. The full audit report is posted to Slack.

Importantly, the agent does NOT write back to Jira. In real teams, only PMs update user stories. The agent's role is to advise — it gives the PM everything they need to improve the story themselves. This makes the agent realistic and safe to run in production.

**Input**

- All Jira stories fetched from Jira — the agent reads the acceptance criteria from the story description field (QA-1 has 12 ACs, QA-2 has 5, QA-3 has 6, QA-7 has full workflow ACs — all pre-seeded)

**Expected Output**

- A detailed Slack message posted to `#qa-reports` containing for each story:
  - Story key and title
  - Completeness score (out of 10)
  - Which scenario types are present (happy path, error, edge case, etc.)
  - Which scenario types are missing
  - Specific suggested ACs to add for each gap, written in Given/When/Then format
- No write-back to Jira — the PM owns story content, the agent only advises

**Recommended Agent Nodes**

```
jira_fetcher → ac_parser → completeness_scorer →
gap_identifier → improvement_suggester → slack_reporter
```

**What Each Node Should Do**

- `jira_fetcher` — Call the Jira search API, filter by `issuetype = Story`, and return each story's key, summary, and full description text. The ACs live inside the description field. Store in state.
- `ac_parser` — Extract and structure the acceptance criteria from each story's description. ACs are usually listed as numbered or bulleted items. Parse them into a clean list per story.
- `completeness_scorer` — For each story's AC list, query RAG for the completeness rubric. Ask the LLM to score the ACs out of 10 and identify which scenario categories are present vs missing (happy path, errors, boundaries, UI feedback, security, persistence).
- `gap_identifier` — Based on the scores, determine which stories have meaningful gaps (score below 8). For each gap category, identify what type of AC is needed.
- `improvement_suggester` — For each identified gap, generate 1–2 specific ACs in Given/When/Then format that the PM can directly add to the story. Use RAG context for AC writing standards.
- `slack_reporter` — Format and post the full audit to `#qa-reports`. Group by story, show score, show missing categories, and include the suggested ACs. Stories scoring 9–10 can be reported as "No action needed".

**RAG Knowledge Base**
- `testing_guidelines.md`
- `acceptance_criteria_standards.md`

**Integrations**
- Jira: read stories and their descriptions (read only — no write)
- Slack: post the full audit report

**Must-Have Requirements**

1. Agent uses the supervisor pattern
2. RAG is used to score each story's ACs against the completeness rubric
3. The Slack report includes specific suggested ACs written in Given/When/Then format — not just "add more edge cases"
4. Memory stores previous audit scores per story — if a story's ACs have not changed since the last run, the agent skips it and reports "no changes detected"
5. The report clearly distinguishes between stories that are complete vs stories needing improvement

**Stretch Goal — Streamlit UI**

A page where the trainer selects a Jira story from a dropdown and sees the real-time AC audit with score, gaps, and suggested additions.

---

## Timeline — 2.5 Hours

| Time      | Activity                                                                                                        |
|-----------|-----------------------------------------------------------------------------------------------------------------|
| 0:00–0:15 | Read the brief, form teams (3–4 people), pick ONE project, sketch the agent flow on paper — boxes and arrows   |
| 0:15–0:35 | Setup — copy KB docs, rebuild RAG index, verify mock services are running, confirm `.env` is configured        |
| 0:35–1:45 | Build — implement state, graph, and nodes one at a time; test each node in isolation before connecting the next |
| 1:45–2:00 | End-to-end run — wire everything together, run the full agent, fix issues                                       |
| 2:00–2:30 | Demo showcase — 1 person per team shares their screen and runs the agent live                                   |

**Build tips:**
- Copy your graph skeleton from `src/graph/jira_testrail_slack/` — the supervisor pattern, state, and graph wiring are identical
- Build and test one node at a time — do not wire the full graph until each node works individually
- Use `get_logger` in every node so you can see execution flow in the terminal
- If you get stuck on integration calls, check `src/integrations/` — the clients are already built

---

## Demo Expectations

Teams will be split into groups. One person in each group volunteers to code on their machine. All team members contribute — discussing prompts, designing nodes, reviewing outputs, planning the demo.

In the last 30 minutes, one person per team shares their screen and runs the agent live in front of the class.

**Your demo must show:**
1. The agent running end-to-end from the terminal or Streamlit UI
2. At least one integration updated — visible in the mock service UI (TestRail or Jira at localhost:4001 or localhost:4002)
3. A Slack message visible in the Slack mock UI at http://localhost:4003/ui
4. Logs in the terminal showing each agent node executing in sequence
5. A 1-minute explanation of the QA problem your agent solves and how it solves it

**Remember:** done is better than perfect. A working agent that runs end-to-end beats polished code that does not run.

---

## Code Reference — Where to Look

| What you need              | Copy from                                              |
|----------------------------|--------------------------------------------------------|
| Graph + supervisor pattern | `src/graph/jira_testrail_slack/graph.py`               |
| State definition           | `src/graph/jira_testrail_slack/state.py`               |
| Router + route_next logic  | `src/graph/jira_testrail_slack/supervisor.py`          |
| Agent node pattern         | `src/graph/jira_testrail_slack/agents/jira_fetcher.py` |
| RAG query in a node        | `src/graph/test_case_rag/nodes.py`                     |
| Memory usage in a node     | `src/graph/test_case_memory/nodes.py`                  |
| Jira client calls          | `src/integrations/jira_client.py`                      |
| TestRail client calls      | `src/integrations/testrail_client.py`                  |
| Slack client calls         | `src/integrations/slack_client.py`                     |
| Streamlit UI registration  | `src/ui/pipeline_registry.py`                          |
