# Acceptance Criteria Standards

## What Makes an Acceptance Criterion Testable?

An acceptance criterion (AC) is testable when a QA engineer can answer YES to all of these:

1. Is there a clear trigger or precondition?
2. Is there a specific, measurable expected outcome?
3. Can I determine pass or fail without ambiguity?
4. Does it describe observable user-facing behavior, not internal implementation?

If any answer is NO, the AC is incomplete or untestable and needs improvement.

---

## The Given / When / Then Format

The preferred format for all acceptance criteria:

```
Given [precondition or system state]
When  [user action or system event]
Then  [expected observable outcome]
```

**Good examples:**
- Given I am on the login page, When I enter a valid username and password and click Login, Then I am redirected to the /dashboard page
- Given I am not logged in, When I navigate directly to /dashboard, Then I am redirected to the login page with the message "Session expired"
- Given the username field is empty, When I click the Login button, Then a validation message "Required" appears below the username field

**Bad examples:**
- "Login should work" — no trigger, no specific outcome
- "The system should be secure" — not measurable, not testable
- "Use JWT for authentication" — implementation detail, not user behavior

---

## AC Completeness Checklist

A well-written story should have ACs that cover all applicable scenarios:

- [ ] **Happy path** — the primary successful user flow with valid inputs
- [ ] **Error / failure scenarios** — what happens when input is invalid or an action fails
- [ ] **Boundary conditions** — empty inputs, maximum length, minimum values, null
- [ ] **Navigation outcomes** — where the user lands after each significant action
- [ ] **UI feedback** — success messages, error messages, loading states, validation hints
- [ ] **Security / access control** — what happens when an unauthorized user attempts the action
- [ ] **Data persistence** — changes made are saved correctly and reflected on reload

---

## AC Completeness Scoring Rubric (out of 10)

| Criteria | Points |
|----------|--------|
| Uses Given/When/Then or equivalent clear structured format | 2 |
| Happy path scenario is covered | 2 |
| At least one error or failure scenario is covered | 2 |
| Expected outcomes are specific and measurable | 2 |
| At least one edge or boundary condition is covered | 1 |
| UI feedback (messages, states) is specified | 1 |

**Score interpretation:**
- 9–10: Complete — QA can begin test case writing immediately
- 7–8: Minor gaps — 1 or 2 scenario types missing, minor additions needed
- 5–6: Major gaps — multiple scenario types missing, rewrite recommended before sprint starts
- Below 5: Incomplete — will lead to missed defects in testing

---

## AC Anti-Patterns to Flag

| Anti-Pattern | Example | Problem |
|--------------|---------|---------|
| Vague expected outcome | "System should work correctly" | Not verifiable — what does "correctly" mean? |
| Only happy path | All ACs describe success scenarios | Testers will miss every error and edge case |
| Implementation detail | "Use Redis to cache the session" | Not a user-observable behavior |
| Too broad | "Login should be secure" | No specific verifiable condition to test against |
| Assumed context | "User clicks the button" | Which button? What page? What state? |
| No boundary condition | Username tested only with valid values | Min length, max length, special chars all untested |
| Passive voice outcome | "Error will be displayed" | By whom? Where? What does it say? |

---

## Common Missing Scenarios by Feature Type

### Login / Authentication Features
- Empty username field submission
- Empty password field submission
- Invalid username with valid password
- Valid username with invalid password
- Account locked after repeated failed attempts
- Redirect destination after successful login
- Session expiry handling

### Form / Input Features
- Maximum character limit enforcement
- Minimum length enforcement
- Special characters and symbols
- Whitespace-only input
- Copy-paste behavior
- Required field left empty

### Search / Filter Features
- No results found state
- Partial match behavior
- Exact match behavior
- Case sensitivity handling
- Special characters in search term
- Empty search submission

### Navigation Features
- Direct URL access without authentication
- Back button behavior after form submission
- Page not found (404) handling

---

## Improvement Suggestions by Gap Type

| Gap Found | Suggested AC to Add |
|-----------|---------------------|
| Missing error scenario | Given [invalid condition], When [user action], Then [specific error message is displayed] |
| Vague expected outcome | Specify: exact redirect URL, exact message text, or exact UI element state |
| Missing boundary condition | Add: empty input, max-length input, minimum value, special characters |
| No UI feedback specified | Add: what message or visual state the user sees on success and on failure |
| Missing security case | Add: Given an unauthenticated user, When [protected action attempted], Then [redirect or error] |
| No data persistence check | Add: After [action], When [user refreshes or re-opens], Then [data is still present] |
