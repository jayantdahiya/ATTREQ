# Product Overview

## Direction

ATTREQ is an AI-assisted personal styling product built around a simple daily mobile habit:

1. capture and organize wardrobe items,
2. receive context-aware outfit suggestions,
3. wear an outfit,
4. give lightweight feedback,
5. improve future suggestions.

The product direction is now **mobile-first**. The current repository contains `apps/api` and `apps/web`, but the next primary client is a planned **React Native app in `apps/mobile`**. The existing web app should be treated as a legacy or supporting client while the mobile experience becomes the main surface.

## Problem

People with enough clothing to form many outfits still default to the same combinations because the decision cost is too high. That cost shows up most often in the morning when the user has limited time, partial context, and no desire to browse their own wardrobe manually.

ATTREQ reduces that decision fatigue by turning an unstructured closet into a searchable, taggable wardrobe and then surfacing a small number of actionable suggestions instead of requiring open-ended planning.

## Target User

The initial user profile remains:

- college students and working professionals,
- users who care about appearance but do not want to spend much time deciding,
- users who already rely on their phone camera, notifications, and location-aware services.

This target profile is one of the main reasons the client strategy has changed. The strongest product moments are inherently native-mobile:

- taking wardrobe photos,
- granting location permission,
- checking suggestions quickly,
- receiving reminders,
- recording outfit feedback with minimal friction.

## Core User Loop

### 1. Wardrobe Setup

The user adds clothing items through camera capture or photo library import. The system stores the image, extracts item attributes, and organizes the wardrobe into categories, colors, seasons, and occasion metadata.

### 2. Daily Recommendation

The app generates a small set of suggestions using wardrobe availability, weather context, recent wear history, and explicit or implicit user preferences.

### 3. Outfit Action

The user can save, wear, dismiss, or rate a suggestion. That action should feed back into future recommendation quality.

### 4. Habit Reinforcement

The product should feel lightweight enough to open daily. Notifications, fast startup, secure session restoration, and smooth media handling matter more than broad feature scope.

## Product Boundaries for the Next Version

The next version should focus on a reliable daily-use loop, not feature expansion.

In scope:

- mobile authentication and session persistence,
- wardrobe capture and upload,
- daily suggestion retrieval,
- outfit wear and feedback tracking,
- notifications and mobile-friendly state restoration.

Out of scope for this version:

- social features,
- affiliate or shopping flows,
- advanced onboarding personalization,
- broad web feature parity,
- large ML redesigns.

## Current and Target Repo Shape

### Present-Day Repo

- `apps/api`: active FastAPI backend
- `apps/web`: existing Next.js web client
- `infra/docker`: infrastructure and container config
- `docs/`: active documentation set

### Planned Repo Target

- `apps/api`: system of record and shared product core
- `apps/mobile`: planned Expo + React Native client and primary user surface
- `apps/web`: legacy or supporting client while the mobile app becomes primary

## Documentation Rules

- Product docs describe the product and user value.
- Current-state docs describe what exists right now.
- Implementation-plan docs describe the mobile-first target state.
- Archive docs preserve the former Next.js/PWA planning material and should not be treated as active direction.
