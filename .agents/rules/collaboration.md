# Collaboration and Branching Rules

## Branch Structure

The project follows a specific branch structure to manage features and integration.

- **`main`**: The production-ready default branch. Protected.
  - **AGENT RULE:** Do NOT push directly to the `main` branch unless the user explicitly tells you to do so.
- **`develop`**: The main integration branch. All features merge here first. Protected.
  - **AGENT RULE:** Do NOT push directly to the `develop` branch unless the user explicitly tells you to do so.

Feature Branches:
- `feature/frontend-segmentation-map`
- `feature/frontend-decision-page`
- `feature/frontend-planification-page`
- `feature/frontend-communication-page`
- `feature/backend-api-routes`
- `feature/db-schema`
- `feature/ml-yield-model`

  - **AGENT RULE:** By default, work should be committed to one of these existing feature branches based on the task. Do NOT create new branches unless explicitly instructed to do so by the user. If you ever must create one, the format is `feature/name-of-new-feature`.

## Branch Protection & PRs

- **Both `main` and `develop` are protected.**
- **Pull Requests (PRs) are mandatory** for merging into `main` or `develop`.
- **Review Requirements**: At least one approving pull request review is required before merging.

When creating or modifying code for this repository, make sure you push to the appropriate feature branch and create a PR to merge into `develop`.
