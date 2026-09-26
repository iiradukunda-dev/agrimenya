# Collaboration and Branching Rules

## Branch Structure

The project follows a specific branch structure to manage features and integration.

- `main`: The production-ready default branch. Protected.
- `develop`: The main integration branch. All features merge here first. Protected.

Feature Branches:
- `feature/frontend-segmentation-map`
- `feature/frontend-decision-page`
- `feature/frontend-planification-page`
- `feature/frontend-communication-page`
- `feature/backend-api-routes`
- `feature/db-schema`
- `feature/ml-yield-model`

## Branch Protection & PRs

- **Both `main` and `develop` are protected.**
- **Pull Requests (PRs) are mandatory** for merging into `main` or `develop`.
- **Review Requirements**: At least one approving pull request review is required before merging.

When creating or modifying code for this repository, make sure you push to the appropriate feature branch and create a PR to merge into `develop`.
