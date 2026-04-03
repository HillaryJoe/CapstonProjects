# Test Case Quality Standards

## Anatomy of a Complete Test Case

A high-quality test case must include all of the following fields:

1. **Title** — Clear and specific, describes what is being tested in one sentence
2. **Preconditions** — The system state, user role, and data required before the test begins
3. **Steps** — Numbered list of actions; one action per step; specific and repeatable
4. **Expected Result** — The specific, measurable, verifiable outcome after the steps
5. **Priority** — Critical / High / Medium / Low with justification
6. **Test Type** — Happy path / Negative / Edge case / Regression

---

## Title Quality Standards

Good title format: `[Action] [Feature] [Condition]`

| Example | Quality |
|---------|---------|
| "Login fails when password field is left empty" | Good — specific, condition is clear |
| "Add to cart updates item count in the header" | Good — feature and outcome stated |
| "Test login" | Bad — too vague, no condition |
| "Check if it works" | Bad — no feature, no condition, not verifiable |

---

## Step Quality Standards

Each step must be:
- A **single, specific action** — do not combine two actions in one step
- Written in **imperative voice**: "Click", "Enter", "Navigate", "Select"
- **Free of ambiguity** — do not say "enter a valid username"; say "enter username: Admin"

Bad step: "Click Login and verify you are redirected to the dashboard"
Good step 1: "Click the Login button"
Good step 2: "Verify the browser URL changes to /dashboard"

---

## Expected Result Standards

Expected results must be:
- **Specific and measurable** — not "page changes" but "user is redirected to /dashboard"
- **Verifiable by anyone** running the test, not just the original author
- **Defined for each key action**, not just the last step
- Never left blank or written as "it should work" or "no errors"

---

## Priority Classification Guide

| Priority | Criteria |
|----------|----------|
| Critical | Core functionality; blocks all other testing if it fails; production-impacting if broken |
| High     | Important feature; regression risk; used in the main user journey |
| Medium   | Secondary feature; affects a subset of users; non-blocking defect |
| Low      | Minor UI issue; cosmetic; rarely executed path |

---

## Completeness Scoring Rubric (out of 10)

| Field | Points |
|-------|--------|
| Title is present and specific (not vague) | 2 |
| Preconditions are defined | 1 |
| Steps are numbered, one action each, and specific | 3 |
| Expected result is specific and measurable | 3 |
| Priority is assigned | 1 |

**Score interpretation:**
- 9–10: High quality, ready for test execution
- 7–8: Minor improvements needed
- 5–6: Significant gaps, needs rework before use
- Below 5: Incomplete, should be rewritten

---

## Common Anti-Patterns to Detect and Flag

| Anti-Pattern | Example | Problem |
|--------------|---------|---------|
| Vague step | "Do something on the settings page" | Cannot be reproduced |
| Missing expected result | Steps listed with no verification | Tester does not know what to check |
| Combined actions in one step | "Click Login and verify redirect" | Two actions in one step |
| Missing preconditions | No user role or data state specified | Test cannot be reproduced reliably |
| Untestable expected result | "User feels satisfied" or "system works well" | Not verifiable |
| Duplicate test case | Same scenario as existing test under different title | Bloats suite, wastes execution time |
| Incorrect priority | Critical smoke test marked Low | Risk mis-prioritised |

---

## Duplicate Detection Rules

Two test cases are likely duplicates when:
- Titles are more than 80% similar after removing common words (the, a, is, should)
- Steps describe the same user action on the same feature in the same order
- Expected results describe the same system outcome

When duplicates are found:
- Flag both test cases
- Recommend keeping the more complete one (higher completeness score)
- Suggest merging or deleting the lower-quality duplicate

---

## Improvement Patterns

| Issue Found | Recommended Fix |
|-------------|-----------------|
| Vague step | Add specific input values, element names, or page URLs |
| Missing expected result | Add what the system should display or do after each action |
| Missing preconditions | Add the required user role, data state, or browser/environment |
| Scope too broad | Split into multiple focused test cases, one scenario each |
| Wrong priority | Re-classify based on business impact and frequency of use |
| Ambiguous input value | Replace "valid input" with the actual test data value |
