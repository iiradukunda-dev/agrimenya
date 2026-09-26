# Backend Collaboration & Contribution Guidelines

Welcome to the backend development of Agri-Menya! This guide outlines how we are going to collaborate efficiently to ensure the backend API and database work seamlessly with the frontend.

## 1. Branching Strategy

We follow a structured branching model to keep our work organized and prevent breaking changes.

- **`main`**: The production-ready branch. **Never push directly to this branch.**
- **`develop`**: The main integration branch. This is where backend and frontend features meet. **Never push directly to this branch.**
- **Feature Branches**: All your daily work should happen in feature branches created off `develop`. 

I've already created some initial backend feature branches for you:
- `feature/db-schema` (For initial database modeling and migrations)
- `feature/backend-api-routes` (For FastAPI endpoints and logic)
- `feature/ml-yield-model` (For integrating the machine learning logic)

*If you need to work on something else, create a new branch using the naming convention `feature/your-feature-name`.*

## 2. Daily Workflow

When starting work on a new feature or continuing an existing one, please follow these steps:

1. **Get the latest `develop` branch**:
   ```bash
   git checkout develop
   git pull origin develop
   ```
2. **Checkout your feature branch** (e.g., db schema):
   ```bash
   git checkout feature/db-schema
   # If it's a new branch you are creating: git checkout -b feature/new-thing
   ```
3. **Commit your changes**: Write clear and descriptive commit messages.
4. **Push your changes**:
   ```bash
   git push origin feature/db-schema
   ```
5. **Open a Pull Request (PR)**: Go to GitHub and open a Pull Request from your feature branch against the `develop` branch.

## 3. Pull Request Rules

To keep the codebase stable, **branch protections are enabled**:
- You cannot merge a PR into `develop` or `main` without at least **one approved review**.
- When your backend code is ready (or if you want feedback), open a PR and request a review from me (the frontend/project manager).
- We will review the code, test the API endpoints if necessary, and approve the merge.

## 4. Frontend-Backend Collaboration

Because we are working in parallel (Frontend and Backend), clear communication about the API is crucial:

- **API Documentation**: Please ensure FastAPI's auto-generated Swagger UI (at `/docs`) is always running and accurate. The frontend will rely on this contract to build the UI components.
- **Data Contracts**: If you change the structure of the JSON returned by an endpoint, please let me know immediately in the PR or via our communication channels.
- **CORS**: Make sure CORS is configured in the backend to allow requests from the Streamlit frontend during local development.
- **Mock Data**: While you are building the real database routes, if possible, provide mocked JSON responses first. This allows the frontend to be built simultaneously without waiting for the database to be fully populated.

Let's build something great!
