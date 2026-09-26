---
trigger: always_on
---

# Coding Standards — the project

## Core Principle

Write production-quality code that is readable, maintainable, secure, testable, and consistent with the existing project architecture.

Before modifying code:

1. Inspect the relevant existing files.
2. Understand how the current implementation works.
3. Reuse existing utilities, components, hooks, and patterns where appropriate.
4. Avoid unnecessary rewrites.
5. Make the smallest change that correctly solves the problem.
6. Consider side effects and dependencies before making changes.

Never modify unrelated files unless the change is genuinely required.

---

## TypeScript

- Use TypeScript throughout the application.
- Prefer explicit, meaningful types.
- Avoid `any`.
- Do not use `@ts-ignore` or `@ts-expect-error` unless there is a documented technical reason.
- Prefer type-safe solutions over type assertions.
- Use `unknown` when the type is genuinely unknown.
- Keep interfaces and types close to the domain where practical.
- Do not duplicate types unnecessarily.

---

## React and Next.js

- Follow the existing Next.js App Router architecture.
- Prefer Server Components by default.
- Use `"use client"` only when client-side functionality is actually required.
- Keep Client Components as small as practical.
- Do not convert Server Components to Client Components unnecessarily.
- Keep business logic out of presentation components where practical.
- Prefer reusable components over duplicated JSX.
- Keep components focused on a single responsibility.
- Use semantic HTML and accessible interactions.
- Preserve existing responsive behavior.

---

## State Management

- Use local React state for genuinely local UI state.
- Use Zustand only when shared client-side state is required.
- Do not introduce global state for data that can remain local.
- Do not duplicate the same state across multiple stores or components.

---

## Database and Prisma

- Use Prisma for database access according to the existing project architecture.
- Do not access the database directly from client components.
- Keep database operations on the server.
- Validate input before database operations.
- Handle database errors explicitly.
- Avoid unnecessary database queries.
- Avoid N+1 query patterns.
- Never expose database credentials or sensitive database information to the client.
- Do not modify the database schema without considering migrations and existing data.

---

## API and Server Code

- Validate external input before processing it.
- Return appropriate HTTP status codes.
- Use consistent response structures.
- Handle expected errors explicitly.
- Do not expose stack traces, secrets, credentials, or internal implementation details to users.
- Keep authentication and authorization checks on the server.
- Never trust data supplied by the client.

---

## Error Handling

- Handle expected errors intentionally.
- Do not silently swallow errors.
- Avoid empty `catch` blocks.
- Provide useful error information to developers without exposing sensitive implementation details to users.
- Preserve useful error context when rethrowing errors.
- Do not use `console.log` as a replacement for proper error handling.

---

## Security

- Never hardcode secrets, API keys, passwords, tokens, or private credentials.
- Read secrets from environment variables or the project's approved secret-management mechanism.
- Never expose server-only environment variables to client-side code.
- Treat all user input as untrusted.
- Validate and sanitize external input where appropriate.
- Do not weaken authentication or authorization checks to make a feature work.
- Do not disable security mechanisms without a documented reason.

---

## Dependencies

Before adding a dependency:

1. Check whether the required functionality already exists in the project.
2. Check existing dependencies.
3. Determine whether the dependency is actually necessary.
4. Consider maintenance, security, bundle size, and compatibility.
5. Prefer existing project dependencies when appropriate.

Do not install packages merely to solve a problem that can reasonably be solved with existing project functionality.

---

## Code Quality

- Prefer simple solutions over unnecessarily clever abstractions.
- Avoid premature abstraction.
- Avoid duplicated logic.
- Keep functions reasonably small and focused.
- Use descriptive names.
- Avoid unexplained magic numbers and strings.
- Remove dead code when it is clearly part of the requested change.
- Do not leave temporary debugging code in production code.
- Preserve existing conventions unless there is a strong reason to change them.

---

## Formatting and Linting

- Follow the project's Prettier configuration.
- Follow ESLint rules.
- Do not disable ESLint rules merely to make a check pass.
- Do not introduce formatting inconsistencies.
- Run linting after relevant code changes.

---

## Changes to Existing Code

Before modifying an existing implementation:

1. Read the relevant code.
2. Identify its purpose and dependencies.
3. Determine whether other components depend on its current behavior.
4. Preserve existing behavior unless the requested change intentionally changes it.
5. Avoid unrelated refactoring.

When refactoring:

- Preserve behavior unless the task explicitly requires behavioral changes.
- Keep the refactor focused.
- Run the relevant tests after each meaningful stage.

---

## Comments and Documentation

Write comments only when they explain something that is not obvious from the code.

Good comments explain:

- Why a non-obvious decision exists.
- Important constraints.
- External API limitations.
- Security considerations.
- Complex business rules.

Do not write comments that simply restate what the code already says.

---

## Completion Standard

Code is not considered complete merely because it compiles.

Before declaring a code task complete:

1. Review the changed files.
2. Run relevant tests.
3. Run TypeScript checks.
4. Run ESLint.
5. Run the production build when the change could affect the build or production behavior.
6. Confirm that no unrelated files were modified.
7. Confirm that no secrets or sensitive information were introduced.

Never claim that a task is complete when verification has not been performed.
