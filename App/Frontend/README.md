# ATTREQ Frontend

A Next.js 15 PWA frontend for the ATTREQ AI Personal Stylist application.

## Features

- **Progressive Web App (PWA)** with offline capabilities
- **Authentication** with JWT tokens and automatic refresh
- **Wardrobe Management** with file upload and item organization
- **Daily Outfit Recommendations** with weather integration
- **Responsive Design** with mobile-first approach
- **Modern UI** built with shadcn/ui components and Tailwind CSS

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Forms**: React Hook Form with Zod validation
- **PWA**: next-pwa
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Update environment variables in `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_UPLOADS_URL=http://localhost:8000/uploads
NEXT_PUBLIC_APP_NAME=ATTREQ
NEXT_PUBLIC_APP_VERSION=1.0.0
```

4. Start development server:
```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## Docker Development

### Using Docker Compose (Recommended)

The frontend is included in the main backend docker-compose.yml:

```bash
cd ../Backend
docker-compose up frontend
```

### Standalone Docker

```bash
# Build image
docker build -t attreq-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 \
  -e NEXT_PUBLIC_UPLOADS_URL=http://localhost:8000/uploads \
  attreq-frontend
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Main dashboard
│   ├── wardrobe/          # Wardrobe management
│   ├── profile/           # User profile
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page (redirects)
│   └── manifest.ts        # PWA manifest
├── components/            # Reusable components
│   ├── ui/                # shadcn/ui components
│   └── navigation.tsx     # Main navigation
├── lib/                   # Utility libraries
│   ├── api/               # API client and services
│   └── utils.ts           # Utility functions
├── store/                 # Zustand stores
│   ├── auth.ts            # Authentication state
│   └── wardrobe.ts        # Wardrobe state
├── middleware.ts          # Route protection
├── next.config.ts         # Next.js configuration
└── Dockerfile            # Docker configuration
```

## API Integration

The frontend communicates with the FastAPI backend through:

- **Authentication API**: Login, register, profile management
- **Wardrobe API**: Upload, manage clothing items
- **Recommendations API**: Get daily outfit suggestions

### Authentication Flow

1. User logs in with email/password
2. Backend returns JWT access token
3. Token is stored in Zustand store with persistence
4. Axios interceptors automatically attach token to requests
5. Token refresh handled automatically on 401 responses

### File Upload

- Supports image files (JPG, PNG) up to 10MB
- Uses FormData for multipart uploads
- Shows upload progress and processing status
- Integrates with backend AI processing pipeline

## PWA Features

- **Offline Support**: Caches static assets and API responses
- **Install Prompt**: Users can install as native app
- **Background Sync**: Handles offline actions when online
- **Push Notifications**: Ready for future implementation

## Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

### Code Style

- **ESLint**: Configured with Next.js recommended rules
- **Prettier**: Code formatting (if configured)
- **TypeScript**: Strict mode enabled
- **Import Order**: Absolute imports with `@/` alias

## Deployment

### Vercel (Recommended)

1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Self-Hosting

1. Build the application:
```bash
npm run build
```

2. Start production server:
```bash
npm start
```

3. Configure reverse proxy (Nginx) for production

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_UPLOADS_URL` | File uploads URL | `http://localhost:8000/uploads` |
| `NEXT_PUBLIC_APP_NAME` | Application name | `ATTREQ` |
| `NEXT_PUBLIC_APP_VERSION` | Application version | `1.0.0` |

## Contributing

1. Follow the existing code style
2. Add TypeScript types for all new features
3. Test with the backend API
4. Update documentation as needed

## License

This project is part of the ATTREQ application suite.