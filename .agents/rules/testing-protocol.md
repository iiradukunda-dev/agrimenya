---
trigger: always_on
---

# Testing Protocol — the project

## 1. Testing Principle

Tests protect behavior, reliability, and maintainability.

Meaningful behavior changes must have appropriate automated test coverage.

Do not add meaningless tests simply to increase test count.

Tests are expected for:

* new features,
* bug fixes,
* API behavior,
* validation logic,
* business logic,
* reusable utilities,
* important component behavior,
* security-sensitive behavior,
* regression-prone changes.

Tests may not be necessary for:

* documentation-only changes,
* formatting-only changes,
* comments-only changes,
* simple configuration changes that do not affect executable behavior.

When uncertain, prefer adding a focused test if the change could introduce a meaningful regression.

---

## 2. Testing Framework

Use:

* **Vitest** for test execution.
* **React Testing Library** for React component behavior.
* **@testing-library/user-event** for realistic user interactions.
* **jsdom** for browser-like testing where required.

Follow the existing project testing configuration.

Do not introduce another testing framework without a clear technical reason.

---

## 3. Test File Placement

Place tests close to the code they test whenever practical.

Use:

```text
[filename].test.ts
```

for:

* utilities,
* server-side functions,
* validation logic,
* API-related logic.

Use:

```text
[filename].test.tsx
```

for:

* React components,
* UI behavior,
* client-side interactions.

Follow existing project conventions when a different structure is already established.

---

## 4. What Tests Should Verify

Tests should focus on observable behavior.

### Happy Paths

Verify expected successful behavior.

### Edge Cases

Consider cases such as:

* empty input,
* missing values,
* invalid values,
* boundary values,
* empty arrays,
* unexpected responses,
* null or undefined values where applicable.

### Error Cases

Verify that expected failures are handled correctly.

Examples:

* invalid input,
* failed database operations,
* API failures,
* unauthorized requests,
* unavailable external services.

### User Interactions

For UI components, test meaningful user behavior such as:

* clicking,
* typing,
* submitting,
* validation feedback,
* loading states,
* error states,
* successful interactions.

Avoid testing implementation details that users cannot observe.

---

## 5. API and Server Testing

For API routes and server-side logic, test where practical:

* valid requests,
* invalid requests,
* validation failures,
* expected errors,
* correct response status,
* important response data,
* security-sensitive behavior.

Do not expose real secrets or credentials in tests.

Use mocks or test doubles for external services when appropriate.

---

## 6. Database Testing

Database-related tests must avoid damaging real production data.

Use appropriate test databases, mocks, or isolated test environments.

Test important behavior such as:

* successful persistence,
* validation failures,
* expected database errors,
* important query behavior.

Do not make tests dependent on a developer's personal production credentials or database.

---

## 7. Mocking

Mock external dependencies when direct access would make tests:

* unreliable,
* slow,
* environment-dependent,
* destructive,
* dependent on external credentials.

Avoid excessive mocking.

Do not mock the code under test merely to make a test pass.

Mocks should represent realistic dependency behavior.

---

## 8. Next.js Testing

When testing Client Components that depend on Next.js APIs, mock required framework utilities appropriately.

Examples may include:

* `next/navigation`,
* `useRouter`,
* `usePathname`,
* other browser-dependent framework behavior.

Do not convert a component to a Client Component merely to make testing easier.

---

## 9. Regression Testing

Every meaningful bug fix should normally include a regression test.

The regression test should:

1. Reproduce the original failure.
2. Verify the expected behavior after the fix.
3. Prevent the same defect from silently returning.

If a regression test is genuinely impractical, document the reason.

---

## 10. Test Quality

Good tests should be:

* deterministic,
* focused,
* readable,
* maintainable,
* independent,
* fast enough for normal development.

Avoid:

* flaky timing assumptions,
* unnecessary sleeps,
* excessive snapshots,
* implementation-detail assertions,
* duplicated test setup,
* tests that depend on execution order.

---

## 11. Verification Workflow

After meaningful code changes, run:

```bash
npm test
```

Then:

```bash
npm run lint
```

Then:

```bash
npx tsc --noEmit
```

Run:

```bash
npm run build
```

when the change can affect production behavior, routing, configuration, dependencies, or the production build.

If a check fails:

1. Read the failure carefully.
2. Determine whether the failure was introduced by the change.
3. Fix the underlying issue.
4. Run the failed check again.
5. Continue until the required checks pass.

Never ignore a failing test simply because it appears unrelated without investigating it.

---

## 12. Test Changes Themselves

When changing existing tests:

1. Understand what behavior the test currently protects.
2. Determine why the test needs to change.
3. Avoid weakening assertions merely to make tests pass.
4. Preserve meaningful coverage.
5. Run the affected tests.

Do not modify tests to hide a regression.

---

## 13. Coverage Philosophy

Coverage percentage is useful as a signal but is not the sole definition of test quality.

Prioritize coverage of:

* critical business logic,
* public API behavior,
* validation,
* security-sensitive operations,
* important user flows,
* regression-prone code.

Do not create artificial tests solely to increase coverage numbers.

---

## 14. Definition of Done

A meaningful behavior change is complete only when:

* appropriate tests were added or updated,
* tests pass,
* lint passes,
* TypeScript checks pass,
* the production build passes when applicable,
* tests verify behavior rather than implementation details,
* no real secrets or production credentials are used,
* and no existing meaningful coverage was unnecessarily weakened.

A documentation-only, formatting-only, or similarly non-behavioral change does not require artificial automated tests.
