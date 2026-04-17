# Client Transition

## Why the Primary Client Is Changing

ATTREQ was initially documented as a PWA-first product. That is no longer the active direction.

The deciding factors are product-fit concerns, not fashion:

- camera and gallery flows are central,
- location and notification workflows matter,
- secure session persistence matters,
- the app should support quick, repeated daily use on a phone.

Those needs are better matched by a native-mobile client than by continued heavy investment in the current PWA.

## New Default Rule

For new frontend product work:

- assume the target client is `apps/mobile`,
- treat `apps/web` as legacy or supporting surface area,
- avoid designing around browser-only constraints unless web support is explicitly required.

## What Stays Shared

Shared across clients:

- backend API contracts
- product domain concepts
- data models
- business rules enforced by the backend

Not expected to be shared one-to-one:

- screen structure
- navigation patterns
- component implementations
- permission flows
- session-storage mechanics

## How to Treat `apps/web`

`apps/web` is still a real part of the repository. It may continue to be used for:

- limited user access,
- admin or debugging convenience,
- temporary support during the transition.

It should not define the long-term product UX or architecture for new client features.

## Migration Rules

1. Do not copy old PWA assumptions into the mobile plan without re-evaluating them.
2. Do not claim `apps/mobile` exists until it is actually scaffolded in the repo.
3. When backend contracts differ from current web behavior, document the contract explicitly instead of preserving accidental web coupling.
4. Archive superseded PWA planning docs instead of silently deleting the context.
5. Keep current-state docs and implementation-plan docs clearly separated.
