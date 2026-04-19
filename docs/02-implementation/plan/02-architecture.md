# System Architecture

## Top-Level View

```text
Users
  |
  +-- Primary Client Baseline: Expo + React Native (`apps/mobile`)
  |
  +-- Existing Supporting Client: Next.js (`apps/web`)
           |
           v
      FastAPI API (`apps/api`)
           |
           +-- PostgreSQL
           +-- Redis
           +-- Weaviate
           +-- File storage / uploads
           +-- External APIs (weather, classification providers)
```

## Client Roles

### `apps/mobile`

The mobile app is the intended primary client. It owns the daily user experience:

- sign in and session bootstrap,
- wardrobe capture from camera or library,
- recommendation consumption,
- wear and feedback actions,
- notifications and habit loops.

### `apps/web` (existing)

The web app is retained as a legacy or supporting client while the mobile app is implemented. It should not drive new product architecture decisions unless a specific web requirement is intentionally preserved.

## Backend Responsibilities

`apps/api` remains the product core. It should continue to own:

- authentication and token lifecycle endpoints,
- user profile data,
- wardrobe item persistence,
- image-processing and metadata workflows,
- outfit persistence and feedback,
- recommendation generation,
- integration with Redis and Weaviate,
- weather-context support.

## Data and Interaction Flow

### Authentication

1. The client authenticates with the API.
2. The client stores refresh-session material securely on device.
3. The client uses access tokens for API requests.
4. The client refreshes access tokens when needed.

### Wardrobe Upload

1. The user selects or captures an image in the mobile client.
2. The client uploads multipart data to the API.
3. The API stores the asset and creates or updates the wardrobe record.
4. Background processing enriches metadata and searchability.

### Recommendations

1. The client requests daily recommendations.
2. The API resolves weather and wardrobe context.
3. The API returns outfit suggestions and related metadata.
4. The client renders suggestions and captures user actions.

### Feedback Loop

1. The user marks an outfit worn or rates it.
2. The API persists the action.
3. Subsequent recommendation requests reuse that signal.

## Mobile App Internal Shape

The planned mobile app should separate route definitions from reusable logic:

```text
apps/mobile/
  app/                # Expo Router routes and layouts
  src/components/     # Reusable UI and feature widgets
  src/features/       # Auth, wardrobe, recommendations, profile
  src/lib/            # API client, query helpers, storage, utilities
  src/store/          # Zustand state
  src/theme/          # Design tokens and shared styling config
```

## Architecture Constraints

- The docs must distinguish between current and planned clients.
- The backend API should be stabilized rather than rewritten.
- Mobile-specific capabilities such as secure storage, notifications, camera access, and permissions belong in the mobile client.
- Shared business logic should stay at the API contract layer, not as forced UI parity between web and mobile.
