---
trigger: always_on
---

# Security Rules — the project

## 1. Core Security Principle

Treat all external input, requests, uploaded data, environment variables, and third-party responses as untrusted unless explicitly validated.

Security must be considered before implementation, not added only after a vulnerability appears.

---

## 2. Secrets and Environment Variables

Never hardcode:

* API keys
* passwords
* database credentials
* authentication secrets
* private tokens
* encryption keys
* service credentials

Use environment variables for server-side secrets.

Never expose server-only secrets through:

* Client Components
* API responses
* logs
* error messages
* public files
* source code

Never use the `NEXT_PUBLIC_` prefix for a secret that must remain server-side.

The `.env` file must never be committed to Git.

Use `.env.example` for documenting required environment variable names without real secret values.

Never copy real production credentials into `.env.example`.

---

## 3. Input Validation

Never trust data received from:

* forms
* API requests
* query parameters
* URL parameters
* cookies
* headers
* external APIs
* CMS content
* client-side state

Validate input before using it in:

* database operations
* authentication
* authorization
* file operations
* external API calls
* business logic

Validation should check the expected:

* type
* format
* length
* allowed values
* required fields
* boundaries

Reject invalid input with an appropriate response.

---

## 4. API Security

API routes must:

1. Validate the request.
2. Authenticate when authentication is required.
3. Authorize the requested operation.
4. Perform the server-side operation.
5. Return only the information the client needs.

Never trust a client-provided user ID, role, permission, or ownership claim.

Do not expose:

* database errors
* stack traces
* environment variables
* internal paths
* credentials
* private configuration

Use appropriate HTTP status codes.

---

## 5. Authentication and Authorization

Authentication determines **who** a user is.

Authorization determines **what** that user is allowed to do.

Never treat authentication as authorization.

Every protected server operation must verify authorization on the server.

Never rely only on:

* hidden UI elements
* disabled buttons
* client-side checks
* route visibility

Client-side restrictions improve user experience but are not security boundaries.

---

## 6. Database Security

All Prisma and PostgreSQL operations must remain server-side.

Never connect to PostgreSQL directly from a Client Component.

Never expose:

* `DATABASE_URL`
* database credentials
* Prisma connection details
* raw database errors

Use parameterized ORM queries or other safe database APIs.

Do not construct SQL queries using untrusted string concatenation.

Validate input before database operations.

Avoid returning unnecessary database fields to clients.

---

## 7. Contact Form Security

The contact form is a public input boundary.

Contact requests must be treated as untrusted input.

Before creating a `ContactMessage`:

* validate the name,
* validate the email,
* validate the subject,
* validate the message,
* enforce reasonable length limits,
* reject malformed requests.

Do not allow the client to provide protected database fields such as:

* `id`
* `createdAt`

The server must control those values.

Do not expose raw Prisma errors to the user.

---

## 8. XSS Prevention

Do not render untrusted HTML directly.

Avoid using `dangerouslySetInnerHTML` unless there is a clear and documented requirement.

When raw HTML is genuinely required:

1. Validate its source.
2. Sanitize it appropriately.
3. Confirm that rendering it is necessary.
4. Keep the trusted boundary as small as possible.

Never assume CMS content is automatically safe.

---

## 9. CSRF and Request Protection

For state-changing operations, consider the application's authentication mechanism and whether CSRF protection is required.

Do not assume that an endpoint is safe merely because it is difficult to access from the UI.

Server-side security checks must protect the actual operation.

---

## 10. File and Upload Security

If file uploads are introduced:

* validate file type,
* validate file size,
* validate file names,
* avoid trusting client-provided MIME types,
* prevent executable files where inappropriate,
* store uploads outside sensitive application paths,
* generate safe server-side file names,
* prevent path traversal.

Never directly use a user-provided file path on the server.

---

## 11. External Services

Treat responses from Sanity and external APIs as untrusted data.

Validate external responses before relying on them for critical operations.

Do not expose external service credentials to the browser.

Keep external-service authentication and API calls on the server whenever credentials are involved.

---

## 12. Error Handling and Logging

Errors shown to users must not reveal sensitive implementation details.

Never expose:

* stack traces
* SQL queries
* credentials
* tokens
* environment variables
* internal server paths

Do not log secrets or sensitive personal information.

Avoid logging complete request bodies when they may contain private data.

Use structured and useful error handling instead of silently ignoring failures.

---

## 13. Dependency Security

Before adding a dependency:

1. Determine whether the functionality already exists.
2. Check whether an existing dependency can solve the problem.
3. Consider the package's maintenance and security.
4. Consider its effect on bundle size.
5. Verify compatibility with the existing project.

Do not add dependencies unnecessarily.

Do not disable security-related package warnings merely to make installation or builds succeed without understanding the reason.

---

## 14. Client/Server Boundary

Server-only functionality must remain server-side.

Do not import server-only modules into Client Components.

Pay particular attention to:

* Prisma
* database clients
* secret-bearing SDKs
* private API clients
* filesystem operations
* server credentials

Before adding `"use client"`, verify that the component actually requires browser-side functionality.

---

## 15. Security Changes

When modifying authentication, authorization, API boundaries, database access, environment variables, or other security-sensitive code:

1. Inspect the existing implementation.
2. Identify the security boundary.
3. Identify affected routes and components.
4. Preserve existing protections.
5. Make the smallest appropriate change.
6. Add or update relevant tests.
7. Run TypeScript checks.
8. Run ESLint.
9. Run relevant tests.
10. Run the production build when applicable.

Never weaken an existing security control simply to make a feature easier to implement.

---

## 16. Security Definition of Done

A security-sensitive change is complete only when:

* secrets remain server-side,
* input is validated,
* authorization is enforced where required,
* database access remains protected,
* sensitive errors are not exposed,
* relevant security tests pass,
* TypeScript passes,
* ESLint passes,
* the production build passes when applicable,
* no secrets were added to Git,
* and no unnecessary security controls were removed.
