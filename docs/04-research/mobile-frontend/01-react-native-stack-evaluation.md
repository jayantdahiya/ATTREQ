# React Native Stack Evaluation

## Decision

Use the following baseline for ATTREQ's planned mobile client:

- Expo
- TypeScript
- Expo Router
- TanStack Query
- Zustand
- React Hook Form
- Zod
- NativeWind
- react-native-reusables
- Expo SecureStore
- Reanimated
- FlashList

## Why This Stack Fits ATTREQ

ATTREQ is naturally mobile-first:

- wardrobe capture is camera and gallery heavy,
- recommendations are checked in short daily sessions,
- auth should restore reliably on device,
- notifications are valuable to reinforce the habit loop.

Expo and React Native fit that product shape better than continued PWA investment.

## Key Decisions

### Expo over a custom bare setup

Expo provides the most practical baseline for:

- fast app bootstrap,
- device testing,
- notifications,
- image and camera workflows,
- build and release tooling.

### Expo Router over making React Navigation the top-level choice

Expo Router gives file-based routing and aligns well with the planned app structure. React Navigation still matters under the hood, but it does not need to be the primary abstraction for this app.

### TanStack Query and Zustand split

- TanStack Query owns server state.
- Zustand owns auth and lightweight app-local state.

This keeps remote data out of ad hoc global stores.

### NativeWind-based UI system

ATTREQ benefits from a flexible, custom product feel more than a rigid off-the-shelf design system. NativeWind keeps styling velocity high while still allowing product-specific UI.

## Notes on Research Inputs

This decision was made using:

- the current repo context,
- current official Expo and library documentation reviewed during planning,
- the research summary provided in the project discussion.

Context7 MCP was requested during the research phase, but its direct tool surface was not exposed in this session, so the final call was based on repo context plus current library documentation and comparisons already gathered.

## Source Links

- [Expo create-expo-app](https://docs.expo.dev/more/create-expo/)
- [Expo Router introduction](https://docs.expo.dev/router/introduction/)
- [Expo Router authentication](https://docs.expo.dev/router/advanced/authentication/)
- [TanStack Query for React Native](https://tanstack.com/query/v5/docs/framework/react/react-native)
- [NativeWind docs](https://www.nativewind.dev/docs/getting-started/installation)
- [react-native-reusables](https://github.com/founded-labs/react-native-reusables)
