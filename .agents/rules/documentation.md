---
trigger: always_on
---

# Documentation Rules — the project

## 1. Documentation Principle

Documentation should make the project easier to understand, maintain, and operate.

Write documentation when it provides meaningful value.

Do not create documentation merely to increase the number of files.

Keep documentation accurate, concise, and consistent with the actual implementation.

---

## 2. Before Writing Documentation

Before creating or changing documentation:

1. Inspect the existing documentation.
2. Check whether the information already exists elsewhere.
3. Reuse existing documentation when appropriate.
4. Avoid creating duplicate documentation.
5. Confirm that the information is accurate.

Do not document assumptions as facts.

---

## 3. README

The root `README.md` should contain useful project-level information such as:

* project purpose,
* major technologies,
* prerequisites,
* installation instructions,
* environment configuration,
* development commands,
* testing commands,
* build instructions,
* deployment information when applicable.

Keep the README aligned with the actual project.

If a command, dependency, environment variable, or workflow changes, consider whether the README needs an update.

---

## 4. Environment Variables

Document required environment variables in `.env.example`.

Never place real credentials or secret values in documentation.

Use safe placeholders such as:

```text
DATABASE_URL=
SANITY_PROJECT_ID=
SANITY_DATASET=
```

Do not copy production credentials into documentation.

---

## 5. Architecture Documentation

When a significant architectural decision is introduced or changed:

1. Determine whether existing architecture documentation should be updated.
2. Document the reason for the decision when it is not obvious.
3. Document important constraints.
4. Keep the documentation consistent with the actual codebase.

Do not document theoretical architecture that the project does not actually use.

---

## 6. Code Comments

Comments should explain **why**, not merely **what**.

Good comments explain:

* non-obvious technical decisions,
* important constraints,
* external API limitations,
* security considerations,
* complex business rules.

Avoid comments that simply repeat the code.

Bad:

```ts
// Set loading to true
setLoading(true);
```

Useful:

```ts
// Keep the request state active until the server confirms persistence.
setLoading(true);
```

---

## 7. API Documentation

When an API becomes significant enough to be consumed by multiple parts of the application or external clients, document:

* endpoint purpose,
* HTTP method,
* expected input,
* validation rules,
* response structure,
* relevant status codes,
* authentication requirements when applicable.

Keep API documentation synchronized with the implementation.

---

## 8. Feature Documentation

For significant features, document information that another developer would need to understand or operate the feature.

Depending on the feature, this may include:

* purpose,
* architecture,
* data flow,
* configuration,
* external services,
* important limitations,
* testing approach.

Do not create a separate document for every small component.

---

## 9. Changelog and Release Information

If the project introduces a changelog or release documentation, keep entries focused on meaningful changes.

Do not document every tiny formatting change.

Describe user-visible or operationally important changes accurately.

Never claim a feature is complete when it is only partially implemented.

---

## 10. Documentation During Development

Do not stop implementation unnecessarily to write extensive documentation for a small change.

For normal changes:

1. Implement the change.
2. Verify the change.
3. Determine whether documentation needs updating.
4. Update only the relevant documentation.

For architectural or operational changes, documentation may need to be updated as part of the same task.

---

## 11. Accuracy

Documentation must reflect the current project.

Never leave outdated instructions when they are known to be incorrect.

When changing:

* commands,
* dependencies,
* environment variables,
* routes,
* architecture,
* database behavior,
* deployment configuration,

check related documentation for stale information.

---

## 12. Documentation Definition of Done

A documentation change is complete when:

* the information is accurate,
* existing documentation was checked,
* duplicate documentation was avoided,
* secrets were not exposed,
* formatting is consistent,
* relevant instructions were verified where practical,
* and unrelated documentation was not modified.
