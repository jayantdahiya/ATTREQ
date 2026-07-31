# M0 — Scaffold & Design System

> **Status:** ✅ Complete (2026-07-15). Gallery verified on simulator in light+dark; adversarial review found 6 issues (dark tab-bar tokens, card shadow radius, tap targets, chip a11y, input autocap, icon metrics) — all fixed and re-verified.
> **Parent:** [`00-goal.md`](00-goal.md) — read it first; this file only adds M0 specifics.

## Objective

`apps/ios/ATTREQ.xcodeproj` builds and launches on the iPhone 17 Pro simulator showing a **component gallery** that renders every design-system piece from `assets/design/ios-redesign-v2/attreq-shared.jsx` in light and dark. SwiftLint/SwiftFormat configured; `ios-ci.yml` added.

## Environment facts (established at kickoff)

- Local backend: **http://localhost:8001** (`uvicorn`, background). Deps run under compose project `attreq-dev` — Postgres on **5433**, Redis on **6380** (ports 5432/6379/8000 are occupied by the unrelated `engram` stack; never touch its containers or the `docker_postgres_data` volume, which belongs to engram despite the name).
- Restart deps: `docker compose -p attreq-dev -f infra/docker/compose.api.dev.yml -f <scratch>/compose.ports-override.yml up -d`
- Migrations: temp ini (localhost:5433) — see scratchpad `alembic.local.ini`.
- `apps/api/.env` gained local-dev entries (DATABASE_URL@5433, generated SECRET_KEY, REDIS 6380, `STORAGE_BACKEND=local`). GROQ/OPENWEATHER keys still missing → classification & weather degrade until provided (matters from M2/M4).

## Project layout

```
apps/ios/
├── ATTREQ.xcodeproj/            # objectVersion 77, buildable-folder (synchronized) groups
│   └── xcshareddata/xcschemes/ATTREQ.xcscheme
├── ATTREQ-Info.plist            # outside the synced folder (avoids duplicate-output); UIAppFonts + usage strings
├── .swiftlint.yml  .swiftformat
└── ATTREQ/                      # synchronized root group — files auto-join the target
    ├── App/                     # ATTREQApp, RootView (M0: hosts the gallery)
    ├── DesignSystem/
    │   ├── Theme/               # Theme.swift (token namespace), Typography.swift
    │   ├── Components/          # Card, UnderlineInput, Chip, Pill, PrimaryButton, MonoLabel, BodyText, GarmentPlaceholder, TabBar, StepNav
    │   ├── Icons/               # AttreqIcon enum → SF Symbol or custom Shape per handoff icon
    │   └── Gallery/             # ComponentGalleryView (M0 root screen)
    └── Resources/
        ├── Assets.xcassets      # semantic colorsets (light+dark) per token table in 00-goal.md
        └── Fonts/               # Cormorant Garamond, DM Sans, IBM Plex Mono (TTF, OFL)
```

Build settings: Swift 6 language mode, iOS 17.0 target, `GENERATE_INFOPLIST_FILE=YES` merged with `ATTREQ-Info.plist`, bundle id `com.attreq.ios`, iPhone only.

## Work packages

| WP | Owner | Files | Content |
|---|---|---|---|
| WP0 | orchestrator | xcodeproj, Info.plist, App/, scheme, CI, lint configs | Serial scaffold; validated by `xcodebuild build` before fan-out |
| WP1 | agent | Resources/Fonts/, DesignSystem/Theme/Typography.swift | Download 3 font families (google/fonts GitHub, OFL), `Font` extensions: `.attreqDisplay(size:weight:italic:)`, `.attreqBody(...)`, `.attreqMono(...)` |
| WP2 | agent | Resources/Assets.xcassets, DesignSystem/Theme/Theme.swift | Colorsets with light/dark from token table; `Theme` namespace (`Theme.bg`, `.surface`, `.text`, `.t2`, `.t3`, `.accent`, `.accentSoft`, `.clay`, `.claySoft`, `.moss`, `.mossSoft`, `.border`, `.borderSoft`) + garment gradients + card shadow style |
| WP3 | agent | DesignSystem/Components/ (core) | Card, UnderlineInput, Chip, Pill, PrimaryButton, MonoLabel, BodyText per `attreq-shared.jsx` measurements |
| WP4 | agent | DesignSystem/Components/ (chrome) + Icons/ + Gallery/ | TabBar (floating pill, 4 tabs), StepNav, GarmentPlaceholder, icon set, ComponentGalleryView composing everything |

WP1–WP4 touch disjoint files and run in parallel after WP0 validates. WP3/WP4 depend on WP1/WP2's *interfaces* (Theme/fonts) — the interface contract is fixed in this doc so they can proceed concurrently; integration build catches drift.

## Exit criteria

1. `xcodebuild -project apps/ios/ATTREQ.xcodeproj -scheme ATTREQ build` succeeds (+ tests target later milestones).
2. App launches on iPhone 17 Pro simulator; gallery shows all components; screenshots captured in light and dark appearance.
3. SwiftLint clean; CI workflow added.
4. Committed on `ios-native` branch.
