# Raspberry Pi Backend Testing Guide

## Scope

This guide is for validating the backend deployment on the Raspberry Pi after deployment changes.

Use current repo paths:

- `apps/api`
- `infra/docker`

Do not rely on legacy pre-restructure path references.

## Validate the Deployment

### 1. Check Service Health

- confirm the API container is running,
- confirm database, Redis, and Weaviate containers are healthy,
- confirm logs do not show repeated startup failure loops.

### 2. Check API Reachability

- hit the backend health endpoint,
- verify API docs or OpenAPI are reachable if enabled,
- test the deployment from another machine on the same network when applicable.

### 3. Check Critical Product Flows

- register or log in with a test user,
- fetch the current user,
- upload a wardrobe item,
- request daily recommendations,
- mark an outfit worn or submit feedback.

### 4. Check Mobile Integration Readiness

- verify the API base URL is reachable from a device or emulator,
- verify HTTPS and certificates if the phone is expected to call the deployed API directly,
- verify upload size and timeout behavior with realistic images.

## Failure Modes to Watch

- container restarts caused by missing environment variables,
- unreachable database or Weaviate instances,
- upload directories mounted incorrectly,
- auth refresh failures,
- device-to-host network reachability problems.
