# ATTREQ - Implementation Plan Overview

## Project Summary
**ATTREQ** is an AI-powered personal stylist PWA that helps users manage their wardrobe and receive daily outfit recommendations. This implementation plan is tailored for solo fullstack development with self-hosting on Raspberry Pi 5.

## Key Project Details

### Technical Stack
- **Frontend**: Next.js 15+ (App Router) + React 18+ + TypeScript
- **Styling**: Tailwind CSS + Shadcn/UI components
- **Backend**: Python 3.11+ + FastAPI
- **Database**: PostgreSQL 15+ with pgvector extension
- **Vector Database**: Weaviate (Docker)
- **File Storage**: Local filesystem on Raspberry Pi (NFS/SATA SSD)
- **Authentication**: JWT-based auth + Google OAuth2
- **Hosting**: Self-hosted on Raspberry Pi 5 (Docker Compose)
- **CI/CD**: GitHub Actions with self-hosted runner

### Development Approach
- **Developer**: Solo fullstack developer
- **Timeline**: 8-10 weeks (side project pace)
- **IDE**: Cursor with AI-assisted development
- **Testing**: Backend unit tests + Playwright for PWA E2E

### Simplified MVP Scope
Based on your preferences, we've simplified:
1. **ATTREQ DNA Profiling**: Manual preference form instead of ML clustering
2. **Calendar Integration**: Manual event dropdown instead of full OAuth sync
3. **Analytics/Monitoring**: Deferred to post-MVP
4. **Marketing/Beta**: Focus on technical implementation first

## Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)
- Raspberry Pi server configuration
- Docker Compose environment
- Database setup (PostgreSQL + Weaviate)
- Repository structure

### Phase 2: Backend Core (Weeks 2-3)
- FastAPI project structure
- Authentication system
- Database models & migrations
- Core API endpoints

### Phase 3: AI/ML Pipeline (Weeks 3-4)
- Roboflow clothing recognition integration
- Background removal (Rembg)
- Weaviate vector embeddings
- Recommendation algorithm (hybrid)

### Phase 4: Frontend Foundation (Weeks 4-6)
- Next.js PWA setup
- Shadcn/UI component library
- Core pages & routing
- State management
- API integration

### Phase 5: Features Implementation (Weeks 6-8)
- Wardrobe management UI
- Photo upload & processing
- Daily outfit suggestions
- Calendar view & history
- Weather integration

### Phase 6: PWA & Testing (Weeks 8-9)
- Service worker configuration
- Offline capabilities
- Progressive enhancement
- Backend unit tests
- Playwright E2E tests

### Phase 7: Deployment & Optimization (Week 10)
- Production Docker Compose
- Nginx reverse proxy
- SSL/TLS setup
- Performance optimization
- Backup strategy

## File Structure
```
implementation-plan/
├── 01-overview.md                 # This file
├── 02-architecture.md             # System architecture & data flow
├── 03-infrastructure.md           # Raspberry Pi & Docker setup
├── 04-backend.md                  # FastAPI backend implementation
├── 05-ai-ml-pipeline.md           # AI/ML components & integration
├── 06-frontend.md                 # Next.js PWA frontend
├── 07-authentication.md           # Auth system (JWT + Google OAuth)
├── 08-testing.md                  # Testing strategy & implementation
├── 09-deployment.md               # Production deployment guide
└── 10-development-workflow.md     # Daily workflow & best practices
```

## Success Metrics (MVP)
- [ ] User can create account and login
- [ ] User can upload wardrobe photos (auto-tagged)
- [ ] User receives 3 daily outfit suggestions
- [ ] PWA installable on mobile devices
- [ ] Works offline (cached data)
- [ ] Response time < 2s for outfit generation
- [ ] 85%+ accuracy for clothing recognition
- [ ] Self-hosted on Raspberry Pi with 99%+ uptime

## Tech Debt & Future Enhancements (V2)
Items deferred from MVP:
- ATTREQ DNA ML clustering (K-means)
- Full Google Calendar OAuth sync
- Analytics (Mixpanel/PostHog)
- Error tracking (Sentry)
- E-commerce integration
- Shopping recommendations
- Social features
- Influencer marketplace

## Documentation Standards
Each implementation file includes:
- ✅ Technical steps with exact commands
- ✅ Tool/technology specifications
- ✅ Dependencies & prerequisites
- ✅ Deliverables & success criteria
- ✅ Estimated time (solo dev)
- ✅ Cursor IDE integration tips

## Getting Started
1. Read `02-architecture.md` for system design overview
2. Follow `03-infrastructure.md` to set up Raspberry Pi
3. Proceed sequentially through backend → AI → frontend
4. Use `10-development-workflow.md` for daily coding practices
5. Deploy using `09-deployment.md` when ready

## Quick Reference - External APIs

**Sign up for these services**:
- Roboflow: https://roboflow.com/ (1000 free API calls/month)
- OpenWeatherMap: https://openweathermap.org/api (1000 calls/day free)
- Google OAuth Console: https://console.cloud.google.com/ (optional)

## Timeline Summary

| Week | Focus Area | Hours | Deliverables |
|------|-----------|-------|--------------|
| 1 | Infrastructure | 20-25h | Raspberry Pi setup, Docker running |
| 2-3 | Backend Core | 40-50h | FastAPI app, auth, database models |
| 3-4 | AI/ML Pipeline | 30-40h | Roboflow, Rembg, Weaviate, algorithm |
| 4-6 | Frontend | 50-60h | Next.js PWA, UI components, API integration |
| 6-8 | Features | 40-50h | Upload, processing, outfit generation |
| 8-9 | Testing | 20-30h | Unit tests, E2E tests, PWA testing |
| 10 | Deployment | 15-20h | SSL, Nginx, CI/CD, optimization |

**Total Estimated Hours**: 215-275 hours over 10 weeks (~25-30 hrs/week)

---

**Next Step**: Review `02-architecture.md` to understand the system design before implementation.