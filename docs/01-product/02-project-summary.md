# Project Summary

## Snapshot

ATTREQ is a wardrobe and outfit recommendation system with a FastAPI backend in `apps/api`, an existing Next.js client in `apps/web`, and a planned React Native client in `apps/mobile`.

The backend already covers the main product domain:

- user accounts and session endpoints,
- wardrobe item storage and image-processing pipeline,
- outfit persistence and feedback,
- recommendation generation,
- Redis-backed caching and supporting services.

The frontend direction has changed. The web app remains useful as implementation history and limited support surface, but the next major client investment is the mobile app.

## Why the Frontend Direction Changed

The product’s strongest workflows are mobile-native:

- camera-first wardrobe capture,
- location permission flows,
- fast daily check-ins,
- secure auth persistence,
- notifications and reminders.

Those are possible in the web client, but they are not the strongest fit for a browser-first experience. The React Native app is intended to become the primary user-facing client because it better matches the product loop.

## Current Technical Baseline

### Backend

- `apps/api`
- FastAPI
- PostgreSQL
- Redis
- Weaviate
- image processing and AI-assisted clothing metadata pipeline

### Current Client

- `apps/web`
- Next.js
- TypeScript
- Zustand, Axios, React Hook Form, and Zod patterns already in use

### Planned Primary Client

- `apps/mobile` (planned, not yet created)
- Expo + React Native
- Expo Router
- NativeWind + react-native-reusables
- TanStack Query + Zustand
- React Hook Form + Zod

## Next Version Goal

The next version is not a feature-maximization release. It is a **usable mobile-first product baseline**:

1. sign in,
2. restore session reliably,
3. add wardrobe items from the phone,
4. get daily suggestions,
5. mark outfits worn or rate them,
6. return the next day.

That goal should drive both implementation and documentation priorities.
