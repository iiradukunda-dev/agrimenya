---
trigger: always_on
---

# Architecture Rules — the project

## 1. Architectural Overview

the project is a Next.js application using the App Router and TypeScript.

The main technologies currently used are:

- Next.js 16
- React 19
- TypeScript
- Prisma
- PostgreSQL
- Sanity
- Vitest
- React Testing Library
- Zustand
- Three.js / React Three Fiber
- GSAP
- ESLint
- Prettier

The architecture should remain modular, predictable, and easy to maintain.

Do not introduce a new architectural pattern without first understanding the existing structure and determining that it is necessary.

---

## 2. Source Directory Structure

The primary application source is located under:

```text
src/
├── app/
├── components/
├── lib/
├── sanity/
├── store/
└── types/
