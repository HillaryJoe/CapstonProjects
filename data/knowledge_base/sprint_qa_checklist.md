# Sprint QA Checklist & Coverage Standards

## What Counts as "Covered"

A Jira story is considered test-covered when:
- At least one test case in TestRail references the story key in its title or description
- The test case has a clear title, numbered steps, and an expected result
- At least one happy path test exists for the story
- For stories with user-facing features: at least one negative or edge case test exists

A story with zero linked test cases in TestRail is considered UNCOVERED.

---

## Minimum Test Case Requirements by Story Type

| Story Type       | Minimum Test Cases | Required Test Types                        |
|------------------|--------------------|--------------------------------------------|
| Feature Story    | 3                  | 1 happy path, 1 negative, 1 edge case      |
| Bug Fix          | 1                  | 1 regression test confirming the fix        |
| Enhancement      | 2                  | 1 happy path, 1 boundary condition test    |
| Technical Debt   | 1                  | 1 smoke test verifying nothing is broken   |
| Spike / Research | 0                  | Not applicable — no testable output        |

---

## Coverage Thresholds

| Coverage %   | Status              | Action Required                                      |
|--------------|---------------------|------------------------------------------------------|
| >= 80%       | Green — Go          | Sprint can proceed to release                        |
| 60% – 79%    | Amber — Caution     | Flag to QA lead, document risk                      |
| < 60%        | Red — Block         | Sprint should not release without additional testing |

---

## Sprint Exit Criteria for QA

Before a sprint can be marked complete:

1. All High and Critical priority stories have at least the minimum required test cases
2. All Critical bugs have at least one regression test in TestRail
3. Overall coverage percentage is at or above the Green threshold (80%)
4. All test cases have expected results defined — no blank expected result fields
5. Test cases for new features have been reviewed by at least one other team member

---

## Test Types Defined

### Happy Path
- Covers the primary intended user flow from start to finish
- Uses valid inputs and a standard user role
- Verifies the positive expected outcome is achieved

### Negative Test
- Covers invalid inputs, missing required data, or unauthorized actions
- Verifies the system handles errors gracefully
- Checks that error messages are descriptive and accurate

### Edge Case Test
- Covers boundary values: minimum, maximum, empty, null, very long strings
- Covers uncommon but valid scenarios not part of the main flow
- Covers concurrency or timing-sensitive scenarios where applicable

### Regression Test
- Verifies that a previously fixed bug does not reappear
- Reproduces the exact failure scenario from the original bug report
- Confirms the expected (correct) behavior now works

---

## Coverage Calculation Formula

```
Coverage % = (Stories with >= 1 test case / Total stories in sprint) x 100
```

Stories with status "Done" that have no test cases still count as uncovered.
Stories with status "Won't Fix" or "Duplicate" are excluded from the calculation.

---

## Sprint Coverage Report — Required Fields

A complete sprint coverage report must include:

- Total number of stories in the sprint
- Number of covered stories (with list)
- Number of uncovered stories (with list, sorted by priority)
- Overall coverage percentage
- Go / Caution / Block recommendation
- For each uncovered story: suggested test case titles to be created
