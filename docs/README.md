# ATTREQ Docs

This docs tree is organized to answer four different questions without mixing them up:

- what exists in the repo today,
- what the product is supposed to become,
- how the implementation should be built,
- and which older planning docs are no longer active.

## Read This First

Use this reading order:

1. `08-beta-readiness/00-immediate-beta-readiness.md` for the active Pi backend + Android beta execution tracker
2. `00-current-status/00-current-status.md`
3. `00-current-status/01-task-tracker.md`
4. `00-current-status/02-next-phase-tickets.md`
5. the relevant file in `02-implementation/plan/`
6. `03-execution/tasks/mobile-tasks-v1.md` for current mobile execution work
7. `04-research/mobile-frontend/` for React Native stack and UI-library decisions
8. `01-product/` for product vision and longer-term intent
9. `03-execution/deployment/` for operational backend hosting notes
10. `99-archive/pre-react-native-transition/` for superseded PWA planning docs

## Source Of Truth Rules

- `00-current-status/` tracks current repo truth.
- `08-beta-readiness/00-immediate-beta-readiness.md` is the active execution tracker for the Raspberry Pi backend and Android GitHub-release beta. It supersedes older VPS+Caddy/EAS assumptions for this beta only.
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
- `apps/mobile` exists as the active mobile client baseline.
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
- `wardrobe-ai-knowledge-base.md`: ~75-source deep-research digest (outfit compatibility, tagging, color science, personalization, industry playbooks, competitors) — the evidence base for `07-recommendation-intelligence/`

### `05-roadmap/`

Use this for the active roadmap to beta launch (created 2026-06-10). Each milestone file is self-contained and executable single-shot by an LLM or developer.

- `00-roadmap-overview.md`: milestone list, dependency graph, sequencing rationale, status table
- `01-milestone-1-production-backend.md`: VPS deploy, R2 storage, prod compose fix
- `02-milestone-2-data-model-contracts.md`: category taxonomy, API contract (TKT-002), geocoding
- `03-milestone-3-complete-outfits.md`: footwear/outerwear slots and scoring
- `04-milestone-4-testing-reliability.md`: test suites, backups, monitoring
- `05-milestone-5-distribution-beta.md`: EAS, TestFlight/Play, mobile Sentry (TKT-009)

### `07-recommendation-intelligence/`

Use this for the recommendation-quality phase that follows beta launch (created 2026-07-22). Research-derived: every task cites its evidence from `04-research/wardrobe-ai-knowledge-base.md`. Each milestone file is self-contained and executable single-shot by an LLM or developer.

- `00-roadmap-overview.md`: milestone list, dependency graph, sequencing rationale, "what NOT to build"
- `01-milestone-1-telemetry-eval-harness.md`: preference-pair logging, event stream, tagging benchmark, outfit eval set
- `02-milestone-2-classifier-schema-v2.md`: expanded fixed-enum tag schema + deterministic CIELAB pixel color
- `03-milestone-3-color-context-scoring.md`: CIELAB color harmony, personal-color prior, context weighting
- `04-milestone-4-composition-explanations.md`: seeded greedy generation, anti-repetition, grey inventory, calibrated explanations
- `05-milestone-5-adaptive-personalization.md`: Bayesian quiz blend, fitted scoring weights, swipe deck, vibe prompt
- `06-milestone-6-embeddings-reranker.md`: FashionCLIP embeddings in Weaviate, feedback propagation, optional LLM re-ranker
- `07-milestone-7-retention-trust.md`: wardrobe stats, multi-photo items, archive semantics, batch-capture onboarding

### `08-beta-readiness/`

Use this for the active invite-only beta phase and the intentionally deferred follow-up work.

- `00-immediate-beta-readiness.md`: executable tracker for the Pi backend, Cloudflare Tunnel/R2, optional-component benchmark, Android release signing, GitHub prereleases, and the physical-device beta gate
- `01-post-beta-backlog.md`: deferred work with triggers, scope, and acceptance criteria so it remains actionable without competing with beta blockers

### `99-archive/`

Use this for non-authoritative historical docs.

- `pre-react-native-transition/`: former Next.js/PWA frontend plan and task docs

## If You Need X, Read Y

- Current project status: `00-current-status/00-current-status.md`
- Done vs pending work: `00-current-status/01-task-tracker.md`
- What should be built next: `08-beta-readiness/00-immediate-beta-readiness.md`; use `08-beta-readiness/01-post-beta-backlog.md` only after the immediate beta gate or when an explicit trigger fires
- Recommendation/AI research evidence: `04-research/wardrobe-ai-knowledge-base.md`
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
