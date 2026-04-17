# Component Library Evaluation

## Decision

Use **NativeWind + react-native-reusables** as the primary UI layer for the planned ATTREQ mobile app.

## Why This Is the Best Fit

### NativeWind

NativeWind fits the desired working style:

- fast composition,
- utility-first styling,
- easy alignment with a custom product look,
- no strong Material or platform-library visual lock-in.

### react-native-reusables

react-native-reusables fits the component ownership model we want:

- copy-and-own primitives,
- shadcn-like ergonomics,
- good base set for buttons, inputs, cards, dialogs, badges, and other standard surfaces.

## How to Use It

Safe default use cases:

- auth screens
- settings and profile screens
- forms
- cards
- badges
- loading and empty states

Areas that should be validated early before broad use:

- select
- tooltip
- menu or popover-heavy interactions
- other portal-sensitive overlays

For ATTREQ's core wardrobe and recommendation experiences, custom product components are still the right call.

## Alternatives Considered

### Tamagui

Strong option if the project later wants deep design-token rigor and substantial shared UI strategy across native and web. Not the best first choice here because the immediate priority is shipping a focused native app quickly.

### gluestack UI

Good fallback if react-native-reusables becomes a blocker. It keeps a composable NativeWind-friendly approach, but the current preference is the shadcn-like developer experience from reusables.

### React Native Paper

Mature and stable, but too opinionated in a Material direction for the current ATTREQ product feel.

## Final Rule

Use react-native-reusables for the base system, but do not let the library dictate the product UX. ATTREQ should still have custom wardrobe, recommendation, and interaction components that are designed for the app itself.
