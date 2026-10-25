---
trigger: always_on
---

# Git Workflow Rules — the project

## 1. Git Safety

Git operations must protect the project's history and working files.

Before performing Git operations that modify repository state:

1. Inspect the current status.
2. Understand which files have changed.
3. Confirm the intended scope of the change.
4. Avoid destructive operations unless explicitly requested.

Never assume that every changed file belongs to the current task.

---

## 2. Inspect Before Changing

Before creating a commit, inspect:

```bash
git status
git diff
```

When useful, also inspect:

```bash
git diff --staged
```

Understand the changes before committing them.

Do not commit blindly.

---

## 3. Focused Changes

Keep commits focused on a single logical change.

Prefer:

* feature changes in one commit,
* bug fixes in one commit,
* documentation changes in one commit,
* configuration changes in one commit,

when practical.

Do not mix unrelated changes simply because they exist in the working tree.

---

## 4. Existing User Changes

Never overwrite, discard, reset, or revert existing user changes without explicit permission.

If unrelated modifications already exist:

1. Identify them.
2. Leave them untouched.
3. Modify only files required for the current task.

Do not use destructive commands to obtain a clean working tree.

---

## 5. Destructive Git Commands

Do not run destructive commands without explicit user authorization.

This includes commands such as:

```bash
git reset --hard
git clean -fd
git checkout -- .
git restore .
```

Do not delete branches, rewrite history, or force-push unless explicitly requested.

---

## 6. Commit Messages

Commit messages should clearly describe the actual change.

Prefer concise conventional-style messages such as:

```text
feat: add contact form validation
fix: handle contact API errors
refactor: simplify navigation state
test: add contact form coverage
docs: update architecture rules
chore: update dependencies
```

Do not create misleading commit messages.

Do not claim a feature is implemented when the commit only contains partial work.

---

## 7. Before Committing

Before creating a commit:

1. Review `git status`.
2. Review the relevant diff.
3. Confirm no secrets are included.
4. Confirm no unrelated files are included.
5. Run the relevant tests.
6. Run TypeScript checks when code changed.
7. Run ESLint when code changed.
8. Run the production build when the change could affect production behavior.

Only commit after the relevant verification passes.

---

## 8. Secrets and Sensitive Files

Never commit:

* `.env`
* private keys
* API credentials
* passwords
* access tokens
* database credentials
* certificates containing private material
* other sensitive configuration

The `.env.example` file may be committed when it contains only placeholder values and variable names.

Before committing, verify that sensitive files are ignored by Git.

---

## 9. Pulling and Rebasing

Before pulling or rebasing when local work exists:

1. Inspect the working tree.
2. Understand local changes.
3. Avoid losing uncommitted work.
4. Resolve conflicts carefully.
5. Re-run relevant verification after conflict resolution.

Do not automatically discard local work to resolve a Git conflict.

---

## 10. Merge Conflicts

When conflicts occur:

1. Identify all conflicted files.
2. Understand both sides of the conflict.
3. Preserve required behavior from both changes when appropriate.
4. Remove conflict markers completely.
5. Review the resulting diff.
6. Run tests and verification.

Never resolve conflicts by blindly choosing one side.

---

## 11. Remote Operations

Before pushing changes:

* verify the current branch,
* verify the intended remote,
* review the commits being pushed,
* ensure no secrets are included.

**CRITICAL BRANCH POLICY:**
* **Do not push to the `main` branch unless explicitly instructed by the user.**
* **Push to the `dev` branch by default for all changes.**

Do not force-push by default.

Use force-push only when explicitly requested and when the consequences are understood.

---

## 12. Branching

Use descriptive branch names when branches are appropriate.

Examples:

```text
feature/contact-form
fix/contact-validation
refactor/navigation
docs/project-rules
chore/dependency-update
```

Avoid vague branch names such as:

```text
test
changes
update
new
stuff
```

Do not create unnecessary branches for trivial changes when the project's workflow does not require them.

---

## 13. Git History

Preserve a clear and understandable project history.

Do not rewrite shared history without explicit authorization.

Do not amend or squash commits that have already been shared with others unless the workflow explicitly requires it.

When history rewriting is requested, confirm the affected commits and consequences before proceeding.

---

## 14. Verification After Git Operations

After significant Git operations such as:

* merge,
* rebase,
* conflict resolution,
* cherry-pick,
* revert,

run the relevant project verification.

At minimum, for code changes:

```bash
npm test
npm run lint
npx tsc --noEmit
```

Run:

```bash
npm run build
```

when the operation may affect production behavior.

---

## 15. Definition of Done

A Git-related task is complete only when:

* the intended files were changed,
* unrelated changes were preserved,
* no secrets are staged,
* the diff has been reviewed,
* the relevant verification passes,
* the commit message accurately describes the change when a commit was requested,
* and the repository remains in an understandable state.
