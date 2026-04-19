# ATTREQ Mobile

The mobile client lives in `apps/mobile` and uses Expo Router.

## Run

```bash
cd apps/mobile
npm install
npm run start
```

Set `EXPO_PUBLIC_API_URL` to your reachable ATTREQ API base URL, for example:

```bash
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api/v1 npm run start
```

## Key Flows

- secure auth bootstrap with Expo SecureStore
- wardrobe upload via library or system camera
- daily recommendations with saved-location fallback
- outfit wear tracking and feedback materialized through `/outfits`
- local daily reminders via Expo Notifications
