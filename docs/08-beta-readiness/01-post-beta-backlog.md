# ATTREQ Post-Beta Backlog — Deferred, Not Forgotten

> **Status:** Deferred backlog; do not pull ahead of `00-immediate-beta-readiness.md` without an explicit user decision or trigger below.
> **Last audited:** 2026-08-12
> **Goal:** Preserve known non-immediate work with enough context, scope, and acceptance criteria for a future LLM or developer to execute each item without relying on chat history.

## How to Use This File

1. Finish the immediate tracker in [`00-immediate-beta-readiness.md`](00-immediate-beta-readiness.md) first.
2. Use beta evidence—not intuition—to select the next item.
3. Move an item into an active milestone document before implementation.
4. Record its owner, target release, dependencies, verification commands, and rollout/rollback plan.
5. When completed, update this file and the current-status docs. A milestone is not complete until its changes are pushed or the user explicitly defers the push.

These are known deferred work packages, not an exhaustive prediction of bugs that real beta users may discover. Beta defects affecting security, data loss, authentication, onboarding completion, uploads, recommendations, or crashes take precedence over this list.

## Priority and Trigger Summary

| ID | Item | Current state | Pull forward when |
|---|---|---|---|
| PB-01 | Forgot-password flow | UI affordance inert; no backend reset endpoint | External testers use real accounts or report lockouts |
| PB-02 | Mobile Sentry | Backend Sentry exists; Android client not instrumented | Before cohort grows beyond tightly supported testers |
| PB-03 | FashionCLIP/vector rollout | Implemented behind flags; real inference previously unexercised | BR-04 passes and recommendation value is demonstrated |
| PB-04 | Real tagging/evaluation datasets | Synthetic fixtures only | Before claiming classifier-quality improvements |
| PB-05 | Personal-color selfie experience | Backend optional/consent-gated; client coverage incomplete | Users request it and privacy UX is approved |
| PB-06 | Pydantic/SQLAlchemy modernization | Runtime warnings; tests pass | Before Pydantic 3/Python upgrade or warning becomes failure |
| PB-07 | Store distribution | GitHub APK beta first | Cohort needs easier updates or Play testing is ready |
| PB-08 | iOS TestFlight distribution | Native iOS client exists and is tested | Apple program/account and beta demand are ready |
| PB-09 | OAuth/social login | Ghost schema/settings; no flow | Password auth demonstrably hurts conversion |
| PB-10 | High availability and hosted infrastructure | Single home Pi by design | Reliability/load exceeds beta constraints |
| PB-11 | Product expansion | Shopping/social/advanced analytics are outside beta core | Core retention and recommendation quality are proven |
| PB-12 | Documentation rebaseline and archive cleanup | Several old status headers are stale | Immediately after beta milestone facts stabilize |

## PB-01 — Forgot-Password Flow

### Current state

- Login shows a forgot-password affordance/label.
- The backend has no reset-request or reset-confirm endpoint.
- The control is intentionally inert in both native-client planning and current Android code.

### Why deferred

An invite-only beta can recover accounts manually, but a wider beta cannot.

### Scope

1. Choose an email provider and domain/sender identity.
2. Add short-lived, single-use, hashed reset tokens.
3. Add request and confirm endpoints with enumeration-safe responses.
4. Add rate limits and invalidate existing sessions as appropriate.
5. Add Android deep link or secure code-entry flow.
6. Add tests for expiry, reuse, wrong user, brute force, and successful login after reset.

### Acceptance criteria

- A user can recover an account without revealing whether arbitrary emails exist.
- Tokens are time-bound, single-use, and never stored in plaintext.
- The visible control is functional and tested end to end.

## PB-02 — Mobile Sentry

### Current state

- Backend Sentry initialization exists and is controlled by `SENTRY_DSN`.
- Android has no Sentry SDK/initialization or release-symbol upload path.

### Trigger

Pull forward before the beta becomes too large for direct tester support, or immediately if unexplained client crashes appear.

### Scope

- install and initialize the current supported React Native Sentry SDK;
- inject DSN and environment without committing secrets;
- set release/dist values that match Android version and Git tag;
- upload source maps/native symbols in CI;
- scrub tokens, photos, location, Style DNA data, and other personal data;
- verify a deliberate test crash/event in the beta project.

### Acceptance criteria

- A beta crash maps to readable application source and the correct release.
- Sensitive request bodies, tokens, photos, and user attributes are not collected.

## PB-03 — FashionCLIP, Weaviate, and Reranker Rollout

### Current state

- FashionCLIP embeddings, vector storage, similarity scoring, feedback propagation, cross-check tooling, and optional LLM reranking are implemented behind flags.
- The Recommendation Intelligence completion record states real FashionCLIP inference was not exercised in the original build environment.
- BR-04 in the immediate tracker requires actual Pi measurements before deciding the beta topology.

### Important distinction

Do not treat these as one on/off feature:

- FashionCLIP creates local image/text vectors.
- Weaviate stores and searches vectors.
- `text2vec-transformers` powers a legacy text-vectorized collection and may be unnecessary for the selected beta path.
- The LLM reranker is a remote provider call and can be evaluated independently.

### Trigger

Pull rollout forward only after BR-04 proves technical viability and an offline/online comparison shows a useful recommendation-quality gain.

### Scope

- backfill embeddings for existing items;
- validate model/version reproducibility and vector dimensions;
- define failure/timeout fallbacks;
- measure recommendation relevance, latency, provider errors, and cost;
- canary behind flags;
- document rollback to heuristic scoring without data loss.

### Acceptance criteria

- Feature-on results beat the documented baseline without destabilizing the Pi.
- Disabling the flags restores the baseline immediately.
- Backfills are resumable and do not block ordinary uploads.

## PB-04 — Real Tagging and Outfit Evaluation Data

### Current state

- Tagging and outfit evaluation harnesses exist.
- The DeepFashion sample in the repository uses synthetic/local fixtures because the real dataset is access-gated.
- `eval_outfits --weights fitted` was previously deferred.

### Trigger

Before claiming measurable tagging/recommendation improvement, changing the classifier schema again, or enabling learned weights broadly.

### Scope

- obtain data under valid license/terms;
- document provenance and avoid committing restricted images;
- create reproducible manifests/checksums;
- label a representative ATTREQ phone-photo set;
- establish baseline metrics and merge gates;
- complete fitted-weight evaluation mode if still relevant.

### Acceptance criteria

- Metrics run against real, legally usable data.
- A future agent can reproduce the benchmark without hidden local files.
- Quality claims include dataset, sample size, metric, and uncertainty.

## PB-05 — Personal-Color Selfie Experience

### Current state

- Backend support is optional, feature-flagged, and requires explicit consent.
- Client experience and broad real-device validation are incomplete/deferred.
- Face images are unusually sensitive and are sent to a third-party provider when enabled.

### Trigger

Only after users request the feature and the privacy/consent/storage policy is explicitly approved.

### Scope

- clear opt-in and skip flow;
- purpose, processor, retention, deletion, and limitation copy;
- camera/photo permission handling;
- no silent reuse for unrelated classification;
- delete/withdraw-consent behavior;
- bias/lighting/skin-tone evaluation;
- observability without capturing the image or derived sensitive values.

### Acceptance criteria

- Consent is informed, reversible, and auditable.
- The feature degrades gracefully and never blocks core onboarding.

## PB-06 — Pydantic and SQLAlchemy Modernization

### Current state

The backend passes all tests but emits deprecation warnings for:

- Pydantic V1-style `@validator`;
- class-based Pydantic `Config`;
- legacy SQLAlchemy `declarative_base()` import;
- transitive `crypt`/passlib behavior approaching newer Python removals.

### Trigger

Before Pydantic 3, a Python runtime upgrade that removes dependencies, or when CI begins treating warnings as errors.

### Scope

- migrate validators to `field_validator`;
- migrate models/settings to `ConfigDict`/current settings patterns;
- use `sqlalchemy.orm.declarative_base` or declarative base classes;
- review password-hashing library compatibility;
- add a warnings budget or fail on newly introduced deprecations.

### Acceptance criteria

- Existing API contracts remain unchanged.
- Backend tests and migrations pass with no targeted deprecation warnings.

## PB-07 — Google Play Distribution

### Current state

- Local APK creation works.
- GitHub Releases is the immediate beta channel.
- There is no completed Play internal/closed testing pipeline.

### Trigger

When testers need automatic updates, sideloading becomes a support burden, or Play production-access timelines require starting the closed-testing clock.

### Scope

- Play Console app and package ownership;
- permanent upload signing key and Play App Signing;
- release AAB generation;
- privacy/data-safety declarations;
- store listing assets and support/privacy URLs;
- internal then closed testing rollout;
- staged rollout and rollback process.

### Acceptance criteria

- A tester receives and updates ATTREQ through Play without manual APK handling.
- The signing identity and package ID remain stable.

## PB-08 — iOS TestFlight Distribution

### Current state

- `apps/ios/` is a complete native SwiftUI implementation with automated tests.
- TestFlight/App Store distribution was explicitly outside its implementation milestones.

### Trigger

When Apple Developer Program/App Store Connect access and an iOS tester cohort are ready.

### Scope

- signing team, bundle ID, certificates, and profiles;
- production API environment selection;
- archive and upload automation;
- privacy manifests/declarations;
- TestFlight groups, feedback, crash symbolication, and release notes.

### Acceptance criteria

- An external/internal TestFlight tester completes the same core beta gate as Android.

## PB-09 — OAuth or Social Login

### Current state

- User schema/settings retain OAuth-related remnants.
- There is no complete endpoint, callback, deep-link, token exchange, or account-linking flow.

### Trigger

Only when beta funnel evidence shows email/password creates meaningful abandonment.

### Scope

- choose provider(s);
- implement mobile-native authorization with PKCE where applicable;
- define account linking/collision rules;
- remove ghost settings for providers not implemented;
- threat-model redirect/deep-link handling;
- test cancellation, revoked consent, duplicate email, and token refresh.

### Acceptance criteria

- No UI advertises a provider without a complete secure flow.
- Account linking cannot silently take over an existing password account.

## PB-10 — Hosted Infrastructure and High Availability

### Current state

- The beta intentionally targets one Raspberry Pi on a home connection.
- Cloudflare Tunnel hides the home IP and avoids inbound forwarding, but it does not solve power, ISP, disk, or single-host failure.

### Trigger

- uptime becomes a product requirement;
- tester load saturates CPU/RAM/upload processing;
- home outages materially affect feedback;
- data durability/compliance exceeds home-hosting risk.

### Scope

- evaluate VPS/managed container and managed PostgreSQL options;
- retain R2 to avoid image migration;
- automate deploys, backups, migrations, health gates, and rollback;
- define availability/error-budget target;
- load test before selecting instance size.

### Acceptance criteria

- Migration is rehearsed and reversible.
- No DNS/API-client update is required when the stable hostname moves.

## PB-11 — Product Expansion

### Candidate work

- shopping/affiliate integrations;
- social/sharing features;
- richer trends and wear analytics;
- concierge digitization/resale flows;
- broader wardrobe acquisition and retention features.

### Trigger

Do not schedule from vision documents alone. Require beta evidence that the core loop—capture wardrobe, receive useful recommendations, wear/feedback, return—is reliable and retained.

### Acceptance criteria for planning

- explicit user problem and cohort;
- measurable outcome;
- privacy/business-model implications;
- self-contained milestone document with code paths and verification;
- no degradation of recommendation trust.

## PB-12 — Documentation Rebaseline and Archive Cleanup

### Current state

- `docs/07-recommendation-intelligence/00-roadmap-overview.md` correctly says all RI milestones are done, while several individual RI files still say `Not started`.
- `docs/00-current-status/01-task-tracker.md`, `docs/Pending.md`, and `docs/05-roadmap/` retain items already implemented by later work, including category normalization, migrations, outfit slots, and parts of R2 storage.
- The older beta roadmap assumes a VPS+Caddy path; the immediate tracker now defines Pi+Cloudflare Tunnel as the active beta path.

### Trigger

Perform after the beta deployment facts are stable so documentation is updated once with verified truth.

### Scope

- reconcile status headers and completion dates;
- mark superseded items with links to implementing commits/milestones;
- update current-status truth and Pending matrix;
- archive plans that should no longer drive execution;
- keep historical rationale without allowing it to override current code.

### Acceptance criteria

- A new agent reading `docs/README.md` reaches the correct active tracker first.
- No active source-of-truth file tells an agent to rebuild work already present in `main`.

## Selection Rule After Beta

Choose the next item using this order:

1. security, privacy, or data-loss defect;
2. crash/auth/onboarding/upload blocker reported by testers;
3. instrumentation needed to understand a high-impact problem;
4. recommendation-quality change supported by evaluation data;
5. distribution improvement that reduces tester friction;
6. maintenance/deprecation work with a concrete deadline;
7. product expansion backed by retention evidence.
