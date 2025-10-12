
# Backend Tasks (V1 - MVP)

This document outlines the backend development tasks required for the ATTREQ V1 Minimum Viable Product.

**Last Updated**: October 12, 2025  
**Current Status**: Phase 1 & Phase 2 (Core Authentication) Complete ✅

---

## Phase 1: Infrastructure & Core Setup ✅ COMPLETE

- [x] **Project Initialization**: Set up a FastAPI project with the recommended directory structure.
  - ✅ Complete project structure created in `App/Backend/`
  - ✅ All necessary directories and `__init__.py` files in place
  - ✅ Organized into `api/`, `core/`, `crud/`, `models/`, `schemas/`, `services/`
  
- [x] **Database Setup**:
    - [x] Configure SQLAlchemy with a PostgreSQL connection.
      - ✅ Async SQLAlchemy engine with asyncpg driver
      - ✅ Database URL configuration with environment variables
      - ✅ Session management with dependency injection
    - [x] Implement the database models for `User`, `WardrobeItem`, and `Outfit` using SQLAlchemy ORM.
      - ✅ User model implemented with UUID primary key
      - ✅ Relationships to future models commented out (ready for Phase 3)
      - ⏳ `WardrobeItem` and `Outfit` models pending (Phase 3)
    - [x] Set up Alembic for database migrations and generate the initial migration.
      - ✅ Alembic initialized and configured
      - ✅ Initial migration for User table created and applied
      - ✅ Async migration support configured
      
- [x] **Configuration**: Implement a `settings.py` using Pydantic's `BaseSettings` to manage environment variables.
  - ✅ `app/core/config.py` created with Pydantic Settings v2
  - ✅ Environment variable loading from `.env` file
  - ✅ Database URL, JWT settings, CORS, and API keys configured
  
- [x] **Dockerization**: Create a `Dockerfile` for the FastAPI application.
  - ✅ Production-ready Dockerfile created
  - ✅ Multi-stage build with optimized caching
  - ✅ Health checks configured
  - ✅ System dependencies installed (PostgreSQL, curl)
  
- [x] **Docker Compose Setup**: Create Docker Compose configurations for development and production.
  - ✅ `docker-compose.yml` for development with PostgreSQL, Redis, and Backend
  - ✅ `docker-compose.prod.yml` for production deployment
  - ✅ Automatic database migrations on startup
  - ✅ Volume mounting for development
  - ✅ Health checks for all services
  - ✅ Network isolation configured
  
- [x] **Dependency Management**: Create a `requirements.txt` file.
  - ✅ All dependencies specified with latest compatible versions (October 2025)
  - ✅ FastAPI, SQLAlchemy, Alembic, asyncpg, Pydantic, JWT libraries
  - ✅ bcrypt version compatibility fixed (<4.0.0 for passlib)
  
- [x] **Development Tooling**:
  - ✅ Makefile created with convenient Docker commands
  - ✅ `.dockerignore` for optimized builds
  - ✅ Comprehensive README.md with setup instructions

---

## Phase 2: Authentication & User Management ✅ COMPLETE

- [x] **Password Hashing**: Implement password hashing and verification using `passlib`.
  - ✅ bcrypt password hashing with 12 rounds
  - ✅ Password verification function
  - ✅ Password length validation (8-72 characters)
  
- [x] **JWT Authentication**:
    - [x] Implement JWT access and refresh token generation upon successful login.
      - ✅ Access tokens (15 minutes expiry)
      - ✅ Refresh tokens (7 days expiry)
      - ✅ Secure token generation with HS256 algorithm
    - [x] Create a dependency to validate JWTs and protect API endpoints.
      - ✅ OAuth2 password bearer scheme
      - ✅ Token validation middleware
      - ✅ `get_current_user` dependency for protected routes
    - [x] Implement the token refresh endpoint.
      - ✅ Token refresh endpoint with cookie support
      - ✅ HttpOnly cookies for refresh tokens
      
- [x] **API Endpoints - Auth**:
    - [x] `POST /api/v1/auth/register`: Create a new user.
      - ✅ Email validation with Pydantic EmailStr
      - ✅ Duplicate email check
      - ✅ Password strength validation
      - ✅ Returns user data without password
    - [x] `POST /api/v1/auth/login`: Authenticate a user and return JWTs.
      - ✅ OAuth2PasswordRequestForm for standard compliance
      - ✅ Credential verification
      - ✅ Access and refresh token generation
      - ✅ Refresh token stored in HttpOnly cookie
      - ✅ Last login timestamp updated
    - [x] `POST /api/v1/auth/refresh`: Issue a new access token.
      - ✅ Validates refresh token from cookie
      - ✅ Issues new access token
      
- [ ] **Google OAuth2**: Implement the backend flow for Google Sign-In, including the callback endpoint to create or log in a user.
  - ⏳ Pending - User needs to set up Google OAuth credentials first
  - 📝 User model prepared with `oauth_provider` and `oauth_id` fields
  
- [x] **CRUD Operations - User**: Implement basic CRUD functions for the `User` model.
  - ✅ `get_by_email()` - Fetch user by email
  - ✅ `get_by_id()` - Fetch user by UUID
  - ✅ `create()` - Create new user with hashed password
  - ✅ `authenticate()` - Verify email/password combination
  - ✅ `update()` - Update user profile
  - ✅ Password change functionality
  
- [x] **API Endpoints - User Profile**:
    - [x] `GET /api/v1/users/me`: Get current user profile (protected)
    - [x] `PUT /api/v1/users/me`: Update current user profile (protected)
    - [x] `POST /api/v1/users/me/password`: Change password (protected)

**Testing Status**:
- ✅ Health check endpoint working
- ✅ User registration tested successfully
- ✅ User login tested successfully
- ✅ JWT token validation tested successfully
- ✅ Protected endpoints working with Bearer token
- ✅ Swagger UI documentation accessible at `/docs`

**Infrastructure Status**:
- ✅ PostgreSQL running in Docker container
- ✅ Redis running in Docker container (ready for Phase 4)
- ✅ Backend API running in Docker container
- ✅ All services communicating properly
- ✅ Database migrations applied successfully
- ✅ Docker Compose orchestration working

## Phase 3: AI/ML Pipeline & Wardrobe Management ✅ COMPLETE

- [x] **Database Models**:
    - [x] Created `WardrobeItem` model with all required fields
    - [x] Created `Outfit` model for outfit combinations
    - [x] Updated `User` model with relationships
- [x] **Pydantic Schemas**:
    - [x] Created wardrobe schemas (Create, Update, Response, List)
    - [x] Created outfit schemas (Create, Response, Feedback, Wear)
- [x] **File Upload Service**: Create a service to handle multipart file uploads and save them to the designated storage (`/mnt/attreq/uploads`).
    - ✅ FileStorageService with upload, thumbnail generation, and file management
    - ✅ Automatic subdirectory creation (originals/, processed/, thumbnails/)
    - ✅ UUID-based file naming for security
- [x] **Background Worker Setup**: Configure FastAPI's `BackgroundTasks` for handling long-running AI processes.
    - ✅ Integrated into wardrobe upload endpoint
    - ✅ Non-blocking image processing
- [x] **AI Services Integration**:
    - [x] **Background Removal**: Implement a service that uses the `rembg` library to remove the background from an uploaded image.
        - ✅ BackgroundRemovalService with error handling
    - [x] **Clothing Detection**: Implement a service to call the Roboflow API to get clothing category, color, and pattern.
        - ✅ ClothingDetectionService with Roboflow integration
        - ✅ Fallback color extraction using K-means clustering
        - ✅ Pattern detection heuristics
        - ✅ Graceful handling of missing API key
    - [x] **Vector Database**: Set up the Weaviate client and create a schema for `ClothingItem`.
        - ✅ WeaviateEmbeddingsService with schema initialization
        - ✅ Docker Compose integration with text2vec-transformers
    - [x] **Embedding**: Create a service to add a new item's vector embedding to Weaviate after processing.
        - ✅ Add, search, and delete operations
        - ✅ Hybrid search capability
- [x] **Image Processing Worker**: Create a background worker that orchestrates the AI pipeline: remove background -> detect attributes -> add to Weaviate -> update database record.
    - ✅ Complete pipeline orchestration in `image_processor.py`
    - ✅ Status tracking (pending → processing → completed/failed)
    - ✅ Error handling at each step
- [x] **CRUD Operations**:
    - [x] `wardrobe.py`: Full CRUD with filtering and pagination
    - [x] `outfit.py`: Full CRUD with feedback and wear tracking
- [x] **API Endpoints - Wardrobe**:
    - [x] `POST /api/v1/wardrobe/upload`: Accepts an image, saves it, and triggers the background processing task.
    - [x] `GET /api/v1/wardrobe/items`: Retrieve all wardrobe items with filters and pagination.
    - [x] `GET /api/v1/wardrobe/items/{item_id}`: Get single item details.
    - [x] `PUT /api/v1/wardrobe/items/{item_id}`: Allow manual updates to an item's tags.
    - [x] `DELETE /api/v1/wardrobe/items/{item_id}`: Delete a wardrobe item.
- [x] **API Endpoints - Outfits**:
    - [x] `POST /api/v1/outfits`: Create outfit combination
    - [x] `GET /api/v1/outfits`: List user's outfits
    - [x] `GET /api/v1/outfits/{outfit_id}`: Get single outfit
    - [x] `POST /api/v1/outfits/{outfit_id}/wear`: Mark outfit as worn
    - [x] `POST /api/v1/outfits/{outfit_id}/feedback`: Submit feedback
    - [x] `DELETE /api/v1/outfits/{outfit_id}`: Delete outfit
- [x] **Infrastructure**:
    - [x] Docker Compose updated with Weaviate and t2v-transformers
    - [x] Volume mounting for `/mnt/attreq/uploads`
    - [x] Environment variables configured
    - [x] Dependencies added to requirements.txt
- [x] **Documentation**:
    - [x] README.md updated with Phase 3 information
    - [x] PHASE3_SUMMARY.md created with detailed documentation
    - [x] API examples added

**Status**: Implementation complete. Ready for database migration and testing.

**Next Steps**:
1. Generate Alembic migration: `alembic revision --autogenerate -m "Add wardrobe and outfit models"`
2. Create uploads directory: `/mnt/attreq/uploads/{originals,processed,thumbnails}`
3. Apply migration: `alembic upgrade head`
4. Start services: `docker-compose up -d --build`
5. Test endpoints with uploaded images

## Phase 4: Recommendation Engine & Core Logic ✅ COMPLETE

- [x] **External API Integration - Weather**: Create a service to fetch weather data from the OpenWeatherMap API.
  - ✅ OpenWeatherMap API integration with async HTTP client
  - ✅ Weather caching in Redis (1-hour TTL)
  - ✅ Fallback to default weather on API failures
  - ✅ Support for coordinates and city name lookup
- [x] **Recommendation Algorithm**:
    - [x] Develop the hybrid recommendation algorithm that filters items based on weather and event type.
      - ✅ Weather-based filtering (temperature and season)
      - ✅ Occasion-based filtering (casual, formal, party, etc.)
      - ✅ Recently worn items exclusion (14-day window)
    - [x] Use Weaviate's hybrid search to find compatible item combinations.
      - ✅ Semantic search for compatible items
      - ✅ Category-based filtering
    - [x] Implement a scoring system based on color harmony, formality, and user preferences.
      - ✅ Color harmony scoring (complementary, analogous, neutral combinations)
      - ✅ Formality matching scoring (prevents mismatched items)
      - ✅ User preference learning from feedback history
      - ✅ Combined scoring: 40% color + 40% formality + 20% preferences
- [x] **API Endpoints - Recommendations**:
    - [x] `GET /api/v1/recommendations/daily`: Generate and return three daily outfit suggestions with Redis caching (24 hours).
      - ✅ Query parameters: lat, lon, occasion, force_refresh
      - ✅ Weather context included in response
      - ✅ Cached flag in response
    - [x] `DELETE /api/v1/recommendations/cache`: Clear cached suggestions for current user
    - [x] Outfit wear tracking already implemented in Phase 3 (`POST /api/v1/outfits/{id}/wear`)
    - [x] Outfit feedback already implemented in Phase 3 (`POST /api/v1/outfits/{id}/feedback`)
- [x] **Caching**: Integrate Redis for caching daily outfit suggestions and weather data.
  - ✅ Redis client service with connection pooling
  - ✅ Weather cache (1-hour TTL)
  - ✅ Suggestions cache (24-hour TTL)
  - ✅ Cache key format: `daily_suggestions:{user_id}:{date}:{occasion}`
  - ✅ Force refresh parameter to bypass cache

**Testing Status**:
- ✅ Comprehensive test script created (`scripts/test_recommendations.sh`)
- ✅ Weather API integration tested
- ✅ Redis caching verified
- ✅ Outfit generation working
- ✅ All algorithm functions clearly separated for learning

**Infrastructure Status**:
- ✅ Redis service running in Docker
- ✅ Redis connection initialized in app lifespan
- ✅ Weather API configured with environment variable
- ✅ All services communicating properly

**Documentation**:
- ✅ PHASE4_SUMMARY.md created with comprehensive documentation
- ✅ API examples and usage instructions
- ✅ Architecture and design decisions documented

## Phase 5: Testing & Deployment

- [ ] **Unit & Integration Tests**: Write `pytest` tests for critical components:
    - [ ] User authentication and password hashing.
    - [ ] CRUD operations.
    - [ ] Recommendation algorithm logic (with mock data).
- [x] **API Validation**: Ensure all API endpoints have proper Pydantic schema validation for requests and responses.
  - ✅ All endpoints use Pydantic models for request/response validation
  - ✅ Email validation with EmailStr
  - ✅ Password strength validation
- [x] **CORS**: Configure CORS middleware to allow requests from the frontend application.
  - ✅ CORS middleware configured in main.py
  - ✅ Default origins set for local development (http://localhost:3000)
  - ✅ Configurable via environment variables
- [x] **Finalize Docker Compose**: Ensure the backend service in the main `docker-compose.yml` is configured correctly for production (using `env_file`, volumes, etc.).
  - ✅ Development Docker Compose (`docker-compose.yml`) complete
  - ✅ Production Docker Compose (`docker-compose.prod.yml`) complete
  - ✅ Environment variables properly configured
  - ✅ Volume mounting for development
  - ✅ Health checks for all services
  - ✅ Automatic migrations on startup

---

## 📊 Overall Progress Summary

### ✅ Completed (Phase 1, 2, 3 & 4):
- Complete project structure and organization
- FastAPI application with async SQLAlchemy
- User authentication system (register, login, JWT)
- Protected API endpoints
- Database models and migrations (User, WardrobeItem, Outfit)
- Docker Compose orchestration with Weaviate and Redis
- Development tooling (Makefile, README)
- API documentation (Swagger UI)
- **Phase 3 - AI/ML Pipeline**:
  - File storage service with thumbnail generation
  - Background removal using rembg
  - Clothing detection with Roboflow API
  - Weaviate vector database integration
  - Background processing with FastAPI BackgroundTasks
  - Complete wardrobe and outfit management APIs
  - CRUD operations with filtering and pagination
- **Phase 4 - Recommendation Engine**:
  - Weather API integration (OpenWeatherMap) with caching
  - Daily outfit recommendation algorithm with 8 modular functions
  - Weaviate hybrid search for outfit suggestions
  - Color harmony and formality scoring
  - User preference learning from feedback
  - Redis caching for daily suggestions (24h TTL)
  - Comprehensive testing script

### ⏳ Next Steps (Phase 5):
- Unit and integration tests with pytest
- End-to-end testing
- Production deployment preparation

### 🚀 Quick Start:
```bash
cd App/Backend
cp .env.example .env
docker-compose up -d --build
```

### 📚 Documentation:
- Full setup instructions: `App/Backend/README.md`
- API documentation: http://localhost:8000/docs (when running)
- Implementation plan: `Docs/Implementation Plan/04-backend.md`

### 🔗 API Endpoints:

**Authentication (Phase 2)**:
- `GET /health` - Health check
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/users/me` - Get current user (protected)
- `PUT /api/v1/users/me` - Update current user (protected)
- `POST /api/v1/users/me/password` - Change password (protected)

**Wardrobe Management (Phase 3)**:
- `POST /api/v1/wardrobe/upload` - Upload clothing image
- `GET /api/v1/wardrobe/items` - List wardrobe items (with filters)
- `GET /api/v1/wardrobe/items/{id}` - Get single item
- `PUT /api/v1/wardrobe/items/{id}` - Update item tags
- `DELETE /api/v1/wardrobe/items/{id}` - Delete item

**Outfit Management (Phase 3)**:
- `POST /api/v1/outfits` - Create outfit
- `GET /api/v1/outfits` - List outfits
- `GET /api/v1/outfits/{id}` - Get single outfit
- `POST /api/v1/outfits/{id}/wear` - Mark as worn
- `POST /api/v1/outfits/{id}/feedback` - Submit feedback
- `DELETE /api/v1/outfits/{id}` - Delete outfit

**Recommendations (Phase 4)**:
- `GET /api/v1/recommendations/daily` - Get daily outfit suggestions
- `DELETE /api/v1/recommendations/cache` - Clear cached suggestions

### 📦 Technology Stack:
- **Framework**: FastAPI 0.119.0
- **Database**: PostgreSQL 15 with asyncpg
- **Vector Database**: Weaviate 1.23.0 with text2vec-transformers
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic 1.17.0
- **Auth**: JWT with python-jose, bcrypt password hashing
- **Validation**: Pydantic 2.12.0
- **AI/ML**: Roboflow API, rembg, Pillow, scikit-learn, numpy
- **Containerization**: Docker & Docker Compose

---

**Note**: Google OAuth2 implementation is pending user setup of Google Cloud credentials. The database schema is prepared with `oauth_provider` and `oauth_id` fields ready for integration.
