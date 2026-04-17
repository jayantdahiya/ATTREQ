# ATTREQ Docs

This docs tree is organized to answer four different questions without mixing them up:

- what exists in the repo today,
- what the product is supposed to become,
- how the implementation should be built,
- and which older planning docs are no longer active.

## Read This First

Use this reading order:

1. `00-current-status/00-current-status.md`
2. `00-current-status/01-task-tracker.md`
3. `00-current-status/02-next-phase-tickets.md`
4. the relevant file in `02-implementation/plan/`
5. `03-execution/tasks/mobile-tasks-v1.md` for current mobile execution work
6. `04-research/mobile-frontend/` for React Native stack and UI-library decisions
7. `01-product/` for product vision and longer-term intent
8. `03-execution/deployment/` for operational backend hosting notes
9. `99-archive/pre-react-native-transition/` for superseded PWA planning docs

## Source Of Truth Rules

- `00-current-status/` tracks current repo truth.
- `02-implementation/plan/` tracks the target mobile-first implementation design.
- `03-execution/tasks/mobile-tasks-v1.md` is the active client execution checklist.
- `04-research/mobile-frontend/` stores the mobile stack decisions that support the active plan.
- `01-product/` contains product vision, PRD material, and positioning context. It is not the source of truth for shipped functionality.
- `99-archive/pre-react-native-transition/` contains superseded Next.js/PWA planning material that is preserved for historical context only.

If there is a conflict:

- code wins over docs,
- `00-current-status/` wins over all other docs,
- active implementation docs win over product vision docs,
- archive docs never override active docs.

## Current Repo Shape

These paths are the current working structure:

- `apps/api` exists and is the active backend service.
- `apps/web` exists and represents the current web client baseline.
- `apps/mobile` is planned but does not exist yet.
- `infra/docker` contains active container orchestration assets.
- `research/` contains model and experimentation assets outside the docs system.

## Folder Map

### `00-current-status/`

Use this for present-day truth.

- `00-current-status.md`: how to interpret the docs and what is currently true
- `01-task-tracker.md`: completed work and pending work
- `02-next-phase-tickets.md`: prioritized remaining work

### `01-product/`

Use this for product context and roadmap intent.

- `01-product-overview.md`: market, vision, users, and PRD-style context
- `02-project-summary.md`: concise technical and product summary

### `02-implementation/plan/`

Use this for the intended implementation design.

- `01-overview.md`: implementation summary and phases
- `02-architecture.md`: system boundaries and data flow
- `03-infrastructure.md`: backend hosting and Raspberry Pi infrastructure
- `04-backend.md`: backend implementation guidance
- `05-ai-ml-pipeline.md`: wardrobe processing and recommendation pipeline
- `06-frontend.md`: authoritative React Native frontend implementation plan
- `07-authentication.md`: mobile auth and session design
- `08-testing.md`: backend and mobile testing plan
- `09-deployment.md`: backend hosting plus mobile distribution/release flow
- `10-development-workflow.md`: day-to-day development workflow
- `11-client-transition.md`: web-to-mobile transition rules

### `03-execution/`

Use this for operational checklists and deployment notes.

- `tasks/mobile-tasks-v1.md`: active mobile execution checklist
- `tasks/backend-tasks-v1.md`: backend execution checklist
- `deployment/`: Raspberry Pi and backend hosting runbooks

### `04-research/`

Use this for decision support and experiments.

- `mobile-frontend/`: React Native stack research and component-library evaluation
- `llm-detection/`: wardrobe image classification experiments and supporting artifacts

### `99-archive/`

Use this for non-authoritative historical docs.

- `pre-react-native-transition/`: former Next.js/PWA frontend plan and task docs

## If You Need X, Read Y

- Current project status: `00-current-status/00-current-status.md`
- Done vs pending work: `00-current-status/01-task-tracker.md`
- What should be built next: `00-current-status/02-next-phase-tickets.md`
- Mobile implementation design: `02-implementation/plan/06-frontend.md`
- Auth/session behavior: `02-implementation/plan/07-authentication.md`
- Mobile test strategy: `02-implementation/plan/08-testing.md`
- Mobile transition policy: `02-implementation/plan/11-client-transition.md`
- Active mobile checklist: `03-execution/tasks/mobile-tasks-v1.md`
- Backend operational deployment notes: `03-execution/deployment/`
- Product vision and long-term scope: `01-product/`
- React Native stack decision: `04-research/mobile-frontend/01-react-native-stack-evaluation.md`
- UI component-library decision: `04-research/mobile-frontend/02-component-library-evaluation.md`
- Historical PWA plan: `99-archive/pre-react-native-transition/`
