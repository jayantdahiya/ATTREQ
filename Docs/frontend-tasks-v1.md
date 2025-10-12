
# Frontend Tasks (V1 - MVP)

This document outlines the frontend development tasks required for the ATTREQ V1 Minimum Viable Product.

## Phase 1: Project Setup & Foundation

- [ ] **Initialize Project**: Set up Next.js 15+ project with TypeScript, Tailwind CSS, and App Router.
- [ ] **PWA Configuration**:
    - [ ] Configure `next-pwa` for service worker generation and offline capabilities.
    - [ ] Create `manifest.json` with app icons and metadata.
    - [ ] Implement a basic service worker for caching core assets.
- [ ] **UI Library**: Install and configure `shadcn/ui`. Initialize core components (`Button`, `Card`, `Input`, `Dialog`, `Label`).
- [ ] **API Client**: Create an Axios instance for API communication. Implement interceptors for automatically attaching JWT tokens to requests and handling token refresh logic on 401 errors.
- [ ] **State Management**: Set up Zustand for managing global state (e.g., user authentication status).
- [ ] **Layout**: Create a main responsive layout component including a navigation bar and footer.

## Phase 2: Authentication & Onboarding

- [ ] **Registration Page**: Build the UI for user registration (`/auth/register`).
- [ ] **Login Page**: Build the UI for user login (`/auth/login`).
- [ ] **Google OAuth**: Implement the client-side flow for Google Sign-In.
- [ ] **Protected Routes**: Create a higher-order component or middleware to protect routes that require authentication.
- [ ] **Style DNA Onboarding**:
    - [ ] Develop the swipeable card interface for the 15-image style quiz.
    - [ ] Implement logic to send the user's preferences to the backend upon completion.

## Phase 3: Core Features

- [ ] **Wardrobe - Upload**:
    - [ ] Create the UI for uploading new wardrobe items via camera or file selection.
    - [ ] Implement the file upload logic, showing a processing/loading state.
    - [ ] Display the AI-generated tags and allow the user to confirm or edit them.
- [ ] **Wardrobe - View**:
    - [ ] Build the main wardrobe page (`/wardrobe`) to display items in a responsive grid.
    - [ ] Implement client-side filtering by category, color, and season.
    - [ ] Implement a search bar to find items by name or tag.
    - [ ] Create a detail view/modal to show a larger image and all associated tags.
    - [ ] Add functionality to delete a wardrobe item.
- [ ] **Dashboard - Daily Suggestions**:
    - [ ] Create the main dashboard (`/dashboard`) to be the home screen for logged-in users.
    - [ ] Fetch and display the three daily outfit suggestions in a swipeable carousel.
    - [ ] Display the relevant weather and calendar event context for the suggestions.
    - [ ] Implement the "Wear This" button to confirm the day's outfit choice.
    - [ ] Implement the "Like" and "Dislike" buttons to capture user feedback.

## Phase 4: Polish & Finalization

- [ ] **Outfit History**:
    - [ ] Create a new page (`/outfits/history`) with a calendar view.
    - [ ] Display the worn outfit thumbnail on each corresponding day in the calendar.
- [ ] **User Profile**: Build a basic user profile page (`/profile`) to display user information and a logout button.
- [ ] **Responsiveness**: Thoroughly test and fix UI issues across major mobile and desktop screen sizes.
- [ ] **Empty States**: Design and implement empty state components for when the wardrobe is empty or no suggestions are available.
- [ ] **Error Handling**: Implement user-friendly error messages for API failures (e.g., failed login, failed upload).
- [ ] **Testing**: Write E2E tests with Playwright for critical user flows (login, upload, view suggestion).
