---
trigger: always_on
---

## Agrimenya Design-System Enforcement

Before creating, modifying, or reviewing UI, read `AGRIMENYA_DESIGN_SYSTEM.md`.

Treat this file as the canonical source of truth for Agrimenya's visual identity, Liquid Glass surfaces, design tokens, component conventions, accessibility, responsive behavior, motion, performance, and UI evaluation.

### Mandatory rules

1. Follow the approved Agrimenya palette, typography, spacing, surface hierarchy, and component patterns.
2. Prefer agricultural imagery and refined Liquid Glass surfaces where appropriate.
3. Preserve readability, accessibility, responsive behavior, and application functionality.
4. Reuse existing components and tokens before creating new ones.
5. Avoid generic layouts, unnecessary decoration, excessive blur, and unoptimized animation.
6. Respect reduced-motion preferences and provide fallbacks for unsupported visual effects.
7. Preserve existing application logic, state, navigation, and integrations.
8. Inspect the rendered interface when the environment supports visual verification.
9. Do not claim tests, visual checks, or skill recognition succeeded unless they were actually verified.
10. Do not mark substantial UI work complete while critical accessibility, functional, or responsive failures remain.

### Skill coordination

Use only the installed skills relevant to the task.

- `frontend-design`: Interface implementation and visual refinement.
- `ui-ux-pro-max`: Usability and responsive design evaluation.
- `theme-factory`: Shared theme tokens and consistency.
- `brand-guidelines`: Agrimenya brand consistency.
- `emil-design-eng`: Design engineering quality.
- `animate`: Purposeful interaction motion.
- `animate-expo`: Expo or React Native animation when applicable.
- `review-animations`: Animation review.
- `improve-animations`: Animation refinement.
- `find-animation-opportunities`: Useful motion opportunities.
- `animation-performance`: Animation performance.
- `animation-vocabulary`: Motion terminology.
- `ai-design-evaluator`: Design-system compliance evaluation.
- `ai-motion-corrector`: Animation correction.
- `ai-style-mapper`: Mapping existing UI to Agrimenya's visual language.
- `apple-design`: Applicable platform-design principles without overriding Agrimenya's brand.

Follow the actual instructions in each installed `SKILL.md`. Do not assume a skill is installed or recognized until verified.

### Quality gate

For substantial UI changes:

1. Inspect the relevant implementation and existing tokens.
2. Implement the requested functionality using Agrimenya conventions.
3. Check accessibility, responsive behavior, motion, and performance.
4. Inspect the rendered result where possible.
5. Evaluate the implementation against the rubric in `AGRIMENYA_DESIGN_SYSTEM.md`.
6. Resolve critical failures before completion.

Target a minimum evaluation score of 85/100. Critical accessibility, functional, or responsive failures must be fixed regardless of the aggregate score.

### Conflict resolution

If the design system conflicts with accessibility or working application functionality, preserve accessibility and core functionality. Choose the closest visually consistent alternative and explain any meaningful deviation.

Do not overwrite existing project-specific instructions when adding or updating these rules.