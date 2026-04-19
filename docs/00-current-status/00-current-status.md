# Current Status Guide

This file explains how to interpret the ATTREQ docs after the frontend direction changed from PWA-first planning to a mobile-first React Native plan.

## What Is Currently True

- `apps/api` exists and is the active backend service.
- `apps/web` exists and is a working baseline web client.
- `apps/mobile` now exists as the active Expo + React Native client baseline.
- React Native is now the next primary frontend direction for ATTREQ.
- The backend, wardrobe pipeline, recommendations, and auth flows already exist in some form.
- The web client remains a legacy/supporting surface and should not be treated as the long-term client direction.
- Mobile implementation now exists, but it still needs dependency installation, device validation, and release hardening before it should be described as production-ready.

## How To Read The Docs

Use this order when evaluating ATTREQ:

1. `01-task-tracker.md` for done vs pending work
2. `02-next-phase-tickets.md` for prioritized remaining work
3. `../02-implementation/plan/` for target-state design
4. `../03-execution/tasks/mobile-tasks-v1.md` for the active client execution checklist
5. `../04-research/mobile-frontend/` for stack decisions
6. `../01-product/` for product vision and market context
7. `../99-archive/pre-react-native-transition/` only if you need historical PWA context

If any doc conflicts with the codebase, the codebase is the final source of truth.

## Important Caveats

- The repo still contains a web client, but that does not make the web client the future source of truth.
- The active implementation plan is mobile-first, and the repo now includes an `apps/mobile` baseline that reflects that direction.
- Active docs are expected to use the current repo layout and mobile-first terminology consistently.
- Product vision docs may still discuss future features such as Style DNA, richer history, shopping integrations, and broader growth plans. Treat those as roadmap intent, not implementation proof.
- Archive docs are preserved for context only and are not authoritative.

## Practical Rules

If asked whether something is already built:

- check `01-task-tracker.md` first,
- then verify against `apps/api`, `apps/mobile`, or `apps/web`,
- never infer it from the mobile plan alone.

If asked how the system should be built going forward:

- check `../02-implementation/plan/`,
- especially `06-frontend.md`, `07-authentication.md`, `08-testing.md`, and `11-client-transition.md`.

If asked what the active client workstream is:

- check `../03-execution/tasks/mobile-tasks-v1.md`.
