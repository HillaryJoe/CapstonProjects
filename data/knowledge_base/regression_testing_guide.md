# Regression Testing Guide

## What Is a Regression Test?

A regression test verifies that a bug which was previously fixed does not reappear in a future release. Every fixed bug should have at least one corresponding regression test added to the test suite before the story is closed.

Regression tests are the QA team's safety net against recurring defects.

---

## When to Write a Regression Test

**Write a regression test when:**
- A bug has been marked as Fixed, Done, or In Progress (write it proactively before it's resolved)
- A previously passing test suite began failing after a code change
- A production incident is linked to a known bug

**Do NOT write regression tests for:**
- Duplicate bugs — link back to the original bug's existing regression test
- Won't Fix bugs — no code change was made, no regression risk
- Bugs caused by infrastructure or third-party dependencies outside your control

---

## Mapping Bug Fields to Regression Test Fields

| Bug Field            | Maps To Regression Test Field | Notes                                               |
|----------------------|-------------------------------|-----------------------------------------------------|
| Bug Summary          | Test Case Title               | Prefix the title with "REG —"                       |
| Steps to Reproduce   | Test Steps                    | Use the exact same steps from the bug report        |
| Expected Behavior    | Expected Result               | What SHOULD happen after the fix                    |
| Actual Behavior      | Description / Notes           | Document what was broken before the fix             |
| Component / Area     | TestRail Section              | Group regression tests by the same component        |
| Priority             | Test Case Priority            | Inherit directly from the bug priority              |
| Environment          | Preconditions                 | Browser, OS, user role, and data state from the bug |
| Bug Key (e.g. QA-4)  | Title and Description         | Always reference the original bug key               |

---

## Regression Test Naming Convention

Format: `REG — [BUG_KEY] — [Feature Area] — [Scenario Being Verified]`

**Examples:**
- `REG — QA-4 — Login — Valid credentials authenticate successfully on first click`
- `REG — QA-5 — Auth — Forgot password link triggers reset email`
- `REG — QA-6 — Search — Partial employee name match returns correct results`

---

## What a Good Regression Test Must Cover

1. **The exact failure scenario** — reproduce the precise conditions that caused the bug
2. **Fix verification** — confirm the expected (correct) behavior now works after the fix
3. **Boundary conditions** — test values just around the failure trigger point
4. **At least one adjacent scenario** — one nearby path to catch unintended side effects

---

## Regression Test Checklist

Before marking a regression test as complete:

- [ ] Title includes the original bug key (e.g. QA-4)
- [ ] Preconditions match the environment where the bug was found
- [ ] Steps exactly reproduce the original bug scenario from the report
- [ ] Expected result matches the "Expected Behavior" field in the bug report
- [ ] Test has been run once and confirmed passing after the fix was applied
- [ ] Description references the original Jira bug key and a one-line summary of the fix

---

## Minimum Regression Test Coverage by Bug Severity

| Bug Severity | Minimum Regression Tests Required | What to Cover                                    |
|--------------|-----------------------------------|--------------------------------------------------|
| Critical     | 2                                 | Exact failure scenario + one boundary condition  |
| High         | 1                                 | Exact failure scenario                           |
| Medium       | 1                                 | Exact failure scenario                           |
| Low          | Optional                          | At team discretion, time permitting              |

---

## Regression Test Quality Criteria

A regression test is high quality when it is:

- **Deterministic** — produces the same result on every run without manual intervention
- **Independent** — does not depend on other tests running before it
- **Specific** — tests exactly the one failure scenario from the bug, nothing broader
- **Fast** — completes within 2 minutes for a manual test
- **Documented** — description clearly states the original bug key, the failure, and what the fix resolved

---

## Common Regression Test Mistakes

| Mistake | Impact | Correct Approach |
|---------|--------|------------------|
| Steps too vague to reproduce | Test is useless — cannot be re-run by another tester | Copy exact steps from bug report |
| No reference to original bug key | Hard to trace back to the bug when the test fails in future | Always include bug key in title and description |
| Testing the entire feature instead of the specific defect | Slow, bloated test; failure is hard to diagnose | Scope to exactly the defect scenario |
| Writing the test after the bug is already closed | Fix may have already been changed; test may not reflect real behavior | Write the test while the bug is still open |
| Marking expected result as "no error" | Vague — testers don't know what specifically to verify | State the exact expected system state or message |
