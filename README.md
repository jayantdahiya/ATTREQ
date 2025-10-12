# ATTREQ - AI-Powered Personal Stylist

[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192.svg)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com/)

**ATTREQ** is an AI-powered personal stylist Progressive Web App (PWA) that eliminates daily outfit decision fatigue for college students and working professionals. Users digitize their wardrobes through photo uploads with automated AI tagging, receive personalized daily outfit suggestions based on weather, calendar events, and style preferences, and track their outfit history to maximize closet utilization while reducing fashion waste.

## 🎯 Project Vision

Become India's most trusted AI-powered personal stylist, helping millions eliminate daily outfit decisions while maximizing wardrobe utility and reducing fashion waste.

## ✨ Key Features

### 🤖 AI-Powered Wardrobe Management
- **Automatic Clothing Recognition**: Upload photos and get instant AI tagging (category, color, pattern)
- **Background Removal**: Automatic image cleanup using rembg
- **Vector Search**: Semantic search for similar clothing items using Weaviate
- **Thumbnail Generation**: Automatic 300px thumbnail creation

### 🌤️ Smart Daily Recommendations
- **Weather Integration**: Real-time weather data from OpenWeatherMap API
- **Context-Aware Suggestions**: Based on temperature, precipitation, and occasion
- **Advanced Scoring Algorithms**:
  - Color harmony scoring (complementary, analogous, neutral combinations)
  - Formality matching (prevents mismatched items)
  - User preference weighting learned from feedback
- **History Tracking**: Avoids suggesting recently worn items (14-day window)

### 🎨 Style Personalization
- **User Preference Learning**: Analyzes past feedback to improve suggestions
- **Occasion-Based Filtering**: Casual, formal, party, business, and more
- **Style DNA Profiling**: Learns individual preferences through interaction history

### ⚡ Performance & Caching
- **Redis Caching**: High-performance caching for weather (1h) and suggestions (24h)
- **Progressive Web App**: Offline capabilities and installable experience
- **Real-time Updates**: Instant outfit suggestions with force refresh option

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js PWA   │────│   FastAPI API   │────│   PostgreSQL   │
│   Frontend      │    │   Backend       │    │   Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
                ┌─────────────┐  ┌─────────────┐
                │    Redis    │  │   Weaviate  │
                │   Cache     │  │   Vector DB │
                └─────────────┘  └─────────────┘
```

### Tech Stack

#### Frontend
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand
- **PWA**: next-pwa for offline support
- **HTTP Client**: Axios with automatic token refresh

#### Backend
- **Framework**: FastAPI 0.119.0
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15 with asyncpg driver
- **Vector Database**: Weaviate 1.23.0 with text2vec-transformers
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with python-jose
- **AI/ML**: Roboflow API, rembg, Pillow, scikit-learn
- **Migrations**: Alembic
- **Code Quality**: Ruff (linter & formatter)

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **File Storage**: Local filesystem with organized uploads
- **External APIs**: OpenWeatherMap for weather data
- **Background Processing**: Async task processing

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Git
- Make (optional, for convenience commands)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ATTREQ

# Navigate to backend directory
cd App/Backend

# Copy environment template
cp .env.example .env

# Start the entire stack
docker-compose up -d --build

# The services will automatically:
# - Start PostgreSQL database
# - Start Redis cache
# - Start Weaviate vector database
# - Run database migrations
# - Start the FastAPI backend server
# - Start the Next.js frontend
```

### Option 2: Using Make Commands

```bash
cd App/Backend

# Copy environment template
cp .env.example .env

# Start development environment
make start

# Or step by step:
make dev-build    # Build and start services
make migrate      # Run database migrations
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
ATTREQ/
├── App/
│   ├── Backend/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/         # API endpoints
│   │   │   ├── core/           # Configuration & security
│   │   │   ├── crud/           # Database operations
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # Business logic
│   │   │       ├── ai/         # AI/ML services
│   │   │       ├── cache/      # Redis caching
│   │   │       ├── external/    # External API integrations
│   │   │       ├── recommendation/ # Recommendation algorithms
│   │   │       └── storage/    # File storage
│   │   ├── alembic/           # Database migrations
│   │   ├── scripts/           # Utility scripts
│   │   ├── tests/             # Test files
│   │   └── uploads/           # File uploads
│   └── Frontend/              # Next.js PWA frontend
│       ├── app/               # App Router pages
│       ├── components/        # React components
│       ├── lib/               # Utility libraries
│       └── store/             # Zustand stores
├── Docs/                      # Project documentation
│   ├── Implementation Plan/   # Detailed implementation docs
│   └── Project Overview.md   # Complete project overview
└── Extras/                    # Additional resources
    ├── ATTREQ-DESIGN/         # Design assets
    ├── ATTREQ-MODEL/          # AI model resources
    ├── ATTREQ-WEB-APP/        # Flutter mobile app
    └── ATTREQ-WEB-LANDING/    # Landing page
```

## 🔧 Configuration

### Environment Variables

Create `.env` file in `App/Backend/` directory:

```bash
# Core Settings
APP_NAME=ATTREQ
APP_ENV=development
APP_DEBUG=false

# Database
DATABASE_URL=postgresql://attreq_user:password@postgres:5432/attreq_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=attreq_db
POSTGRES_USER=attreq_user
POSTGRES_PASSWORD=your_password

# Authentication
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Weaviate
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
WEAVIATE_SCHEME=http

# External APIs
OPENWEATHER_API_KEY=your_openweather_api_key
ROBOFLOW_API_KEY=your_roboflow_api_key

# File Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/app/uploads
```

### Frontend Environment

Create `.env.local` file in `App/Frontend/` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_UPLOADS_URL=http://localhost:8000/uploads
NEXT_PUBLIC_APP_NAME=ATTREQ
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## 📚 API Documentation

### Core Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

#### Wardrobe Management
- `POST /api/v1/wardrobe/upload` - Upload clothing item with AI processing
- `GET /api/v1/wardrobe/items` - Get user's wardrobe items
- `PUT /api/v1/wardrobe/items/{id}` - Update item details
- `DELETE /api/v1/wardrobe/items/{id}` - Delete item

#### Recommendations
- `GET /api/v1/recommendations/daily` - Get daily outfit suggestions
- `DELETE /api/v1/recommendations/cache` - Clear cached suggestions

#### Outfit Management
- `POST /api/v1/outfits` - Create outfit combination
- `POST /api/v1/outfits/{id}/wear` - Mark outfit as worn
- `POST /api/v1/outfits/{id}/feedback` - Provide feedback on outfit

### Example API Usage

```bash
# Register a user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "full_name": "John Doe",
    "location": "New York"
  }'

# Get daily outfit suggestions
curl -X GET "http://localhost:8000/api/v1/recommendations/daily?lat=40.7128&lon=-74.0060&occasion=casual" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🧪 Testing

### Backend Testing

```bash
cd App/Backend

# Run comprehensive recommendation tests
./scripts/test_recommendations.sh

# Run wardrobe API tests
./scripts/test_wardrobe_api.sh

# Run unit tests
make test
```

### Frontend Testing

```bash
cd App/Frontend

# Run development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint
```

## 🚀 Development Workflow

### Backend Development

1. **Make Changes**: Edit code in the `app/` directory
2. **Run Code Quality**: `make quality` to lint and format
3. **Test Locally**: Use interactive docs at `/docs`
4. **Run Migrations**: If models changed, create and apply migrations
5. **Test Endpoints**: Use curl or Postman to test API endpoints

### Frontend Development

1. **Start Backend**: Ensure backend services are running
2. **Start Frontend**: `npm run dev` in Frontend directory
3. **Make Changes**: Edit components and pages
4. **Test Integration**: Verify API communication
5. **Build for Production**: `npm run build`

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🔒 Security Features

- **Password Hashing**: bcrypt with 12 rounds
- **JWT Tokens**: Secure token-based authentication with refresh tokens
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic schema validation on all endpoints
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **File Upload Security**: Size limits and type validation
- **Environment Variables**: Sensitive data stored securely

## 📊 Current Implementation Status

### ✅ Completed Phases

#### Phase 1 & 2: Core Backend
- User authentication and management
- Secure API with JWT tokens
- PostgreSQL database integration
- API documentation with Swagger UI

#### Phase 3: AI/ML Pipeline
- Wardrobe management with photo uploads
- AI-powered clothing recognition (Roboflow)
- Background removal (rembg)
- Vector search with Weaviate
- Outfit creation and tracking
- Thumbnail generation

#### Phase 4: Recommendation Engine
- Weather integration (OpenWeatherMap)
- Daily outfit recommendations
- Advanced scoring algorithms
- Redis caching for performance
- User preference learning
- Semantic search for compatibility

### 🚧 In Progress

#### Phase 5: Testing & Deployment
- Comprehensive unit and integration tests
- Performance testing and optimization
- Production deployment preparation

### 📋 Future Phases (V2)

- **Style DNA Profiling**: Swipe-based onboarding for style preferences
- **Calendar Integration**: Google Calendar sync for event-based suggestions
- **Social Features**: Outfit sharing and community features
- **E-commerce Integration**: Shopping recommendations and affiliate links
- **Advanced Analytics**: Wardrobe utilization and style insights
- **Mobile Apps**: Native iOS and Android applications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the existing code style and structure
4. Add tests for new functionality
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Quality Standards

- **Backend**: Use Ruff for linting and formatting
- **Frontend**: Use ESLint and TypeScript strict mode
- **Documentation**: Update README and API docs for new features
- **Testing**: Add tests for all new functionality
- **Commits**: Use conventional commit messages

## 📄 License

This project is part of the ATTREQ fashion technology platform. All rights reserved.

## 🆘 Support

### Documentation
- **Complete Project Overview**: [Docs/Project Overview.md](Docs/Project Overview.md)
- **Implementation Plan**: [Docs/Implementation Plan/](Docs/Implementation Plan/)
- **Backend Documentation**: [App/Backend/README.md](App/Backend/README.md)
- **Frontend Documentation**: [App/Frontend/README.md](App/Frontend/README.md)

### Troubleshooting

#### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL container is running: `docker ps`
   - Check database credentials in `.env`
   - Verify database URL format

2. **Redis Connection Failed**
   - Check Redis service: `docker-compose ps`
   - Verify Redis settings in `.env`

3. **Weather API Errors**
   - Check `OPENWEATHER_API_KEY` in `.env`
   - Verify API key validity at OpenWeatherMap

4. **No Suggestions Generated**
   - Ensure sufficient wardrobe items (minimum 2, recommended 5+)
   - Check item processing status
   - Try different occasion types

### Getting Help

- Check the comprehensive documentation in the `Docs/` directory
- Review API documentation at `/docs` endpoint
- Run test scripts to verify setup
- Check logs: `docker-compose logs backend`

---

**ATTREQ** - Your AI-powered personal stylist that knows your wardrobe better than you do! 🎨✨
