# ATTREQ Backend API

AI-powered personal stylist API for wardrobe management and outfit recommendations.

## Overview

ATTREQ is a comprehensive fashion technology platform that combines AI-powered clothing recognition, weather integration, and personalized styling recommendations to help users create perfect outfits for any occasion.

## Features

### Phase 1 & 2 (Complete ✅)
- **User Authentication**: JWT-based authentication with registration and login
- **User Management**: Profile management and account settings
- **Secure API**: Password hashing, token validation, and CORS protection
- **Database Integration**: PostgreSQL with async SQLAlchemy
- **API Documentation**: Interactive Swagger UI at `/docs`

### Phase 3 (Complete ✅)
- **Wardrobe Management**: Upload and manage clothing items
- **AI-Powered Tagging**: Automatic clothing category, color, and pattern detection
- **Background Removal**: Automatic image background removal using rembg
- **Vector Search**: Semantic search for similar clothing items using Weaviate
- **Outfit Creation**: Create and manage outfit combinations
- **Outfit Tracking**: Mark outfits as worn and provide feedback
- **Thumbnail Generation**: Automatic 300px thumbnail creation

### Phase 4 (Complete ✅)
- **Weather Integration**: Real-time weather data from OpenWeatherMap API
- **Daily Outfit Recommendations**: AI-generated outfit suggestions based on:
  - Current weather conditions (temperature, precipitation)
  - Occasion type (casual, formal, party, business)
  - User style preferences learned from feedback
  - Recently worn items (avoid repetition)
- **Advanced Scoring Algorithms**:
  - Color harmony scoring (complementary, analogous, neutral combinations)
  - Formality matching (prevents mismatched items)
  - User preference weighting
- **Redis Caching**: High-performance caching for weather (1h) and suggestions (24h)
- **Semantic Search**: Weaviate hybrid search for compatible item combinations

## Tech Stack

- **Framework**: FastAPI 0.119.0
- **Database**: PostgreSQL 15 with asyncpg driver
- **Vector Database**: Weaviate 1.23.0 with text2vec-transformers
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt via passlib
- **AI/ML**: Roboflow API, rembg, Pillow, scikit-learn
- **Migrations**: Alembic
- **Code Quality**: Ruff (linter & formatter)
- **Containerization**: Docker & Docker Compose
- **Python**: 3.11+

## Project Structure

```
App/Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py         # API router aggregation
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py    # Authentication endpoints
│   │           └── users.py   # User management endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Application settings
│   │   ├── database.py        # Database configuration
│   │   └── security.py        # Security utilities
│   ├── crud/
│   │   ├── __init__.py
│   │   └── user.py           # User CRUD operations
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py           # User SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py           # User Pydantic schemas
│   │   └── token.py          # Token schemas
│   └── services/
│       └── __init__.py
├── alembic/                   # Database migrations
├── tests/                     # Test files
├── .env.example              # Environment variables template
├── .env                      # Environment variables (local)
├── .gitignore
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container configuration
├── docker-compose.dev.yml    # Local development services
├── alembic.ini              # Alembic configuration
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Docker Desktop
- Git
- Make (optional, for convenience commands)

### Option 1: Docker Compose (Recommended)

```bash
# Navigate to backend directory
cd App/Backend

# Copy environment template
cp .env.example .env

# Start the entire stack with Docker Compose
docker-compose up -d --build

# The services will automatically:
# - Start PostgreSQL database
# - Run database migrations
# - Start the FastAPI backend server
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Option 2: Using Make Commands (Convenience)

```bash
# Navigate to backend directory
cd App/Backend

# Copy environment template
cp .env.example .env

# Start development environment (builds, starts, and runs migrations)
make start

# Or step by step:
make dev-build    # Build and start services
make migrate      # Run database migrations
```

### Option 3: Manual Docker Compose Commands

```bash
# Navigate to backend directory
cd App/Backend

# Copy environment template
cp .env.example .env

# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 4: Local Development (Without Docker)

If you prefer to run locally without Docker:

```bash
# Navigate to backend directory
cd App/Backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Start PostgreSQL container only
docker-compose -f docker-compose.dev.yml up -d postgres

# Wait for PostgreSQL to start (about 10 seconds)
sleep 10

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (client-side)

### User Management

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `POST /api/v1/users/change-password` - Change password
- `DELETE /api/v1/users/me` - Deactivate account

### System

- `GET /` - API information
- `GET /health` - Health check

## Testing the API

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123",
    "full_name": "Test User",
    "location": "New York"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"
```

### 3. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Upload Wardrobe Item (Phase 3)

```bash
curl -X POST "http://localhost:8000/api/v1/wardrobe/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/clothing/image.jpg"
```

### 5. List Wardrobe Items

```bash
curl -X GET "http://localhost:8000/api/v1/wardrobe/items?category=shirt&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Create Outfit

```bash
curl -X POST "http://localhost:8000/api/v1/outfits" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "top_item_id": "uuid-of-top-item",
    "bottom_item_id": "uuid-of-bottom-item",
    "occasion_context": "casual"
  }'
```

## Environment Variables

### Core Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | ATTREQ |
| `APP_ENV` | Environment | development |
| `APP_DEBUG` | Debug mode | false |

### Database
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `POSTGRES_HOST` | PostgreSQL host | localhost |
| `POSTGRES_PORT` | PostgreSQL port | 5432 |
| `POSTGRES_DB` | Database name | attreq_db |
| `POSTGRES_USER` | Database user | attreq_user |
| `POSTGRES_PASSWORD` | Database password | Required |

### Authentication
| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 15 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | 7 |
| `BACKEND_CORS_ORIGINS` | CORS allowed origins | ["http://localhost:3000"] |

### Phase 3: AI/ML Services
| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis host | redis |
| `REDIS_PORT` | Redis port | 6379 |
| `REDIS_PASSWORD` | Redis password | Optional |
| `WEAVIATE_HOST` | Weaviate host | weaviate |
| `WEAVIATE_PORT` | Weaviate port | 8080 |
| `WEAVIATE_SCHEME` | Weaviate scheme | http |
| `ROBOFLOW_API_KEY` | Roboflow API key for clothing detection | Optional |
| `ROBOFLOW_MODEL_ID` | Roboflow model ID | clothing-detection-ev04d/4 |
| `ROBOFLOW_PROJECT` | Roboflow project | main-project-qsu9x |
| `OPENWEATHER_API_KEY` | OpenWeather API key | Optional |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size | 10 |
| `UPLOAD_DIR` | Upload directory path | /app/uploads |

## Phase 3 Setup

### Prerequisites
1. Create the uploads directory structure:
```bash
# Create directories
sudo mkdir -p /mnt/attreq/uploads/{originals,processed,thumbnails}
sudo chmod -R 755 /mnt/attreq/uploads

# Or use the provided script
chmod +x scripts/setup_uploads_dir.sh
sudo ./scripts/setup_uploads_dir.sh
```

2. (Optional) Set up Roboflow API:
   - Sign up at https://roboflow.com/
   - Get your API key
   - Add to `.env`: `ROBOFLOW_API_KEY=your_key_here`

3. Database migration for Phase 3 models:
```bash
# Generate migration
alembic revision --autogenerate -m "Add wardrobe and outfit models"

# Apply migration
alembic upgrade head
```

### Services

Phase 3 adds the following Docker services:
- **Weaviate**: Vector database for semantic search (port 8080)
- **t2v-transformers**: Text-to-vector transformer model for Weaviate
- **Redis**: Already present, now utilized for caching
- **Backend**: Enhanced with AI/ML capabilities

Start all services:
```bash
docker-compose up -d --build
```

### Verify Installation

```bash
# Check Weaviate is running
curl http://localhost:8080/v1/.well-known/ready

# Check Redis is running
docker exec attreq_redis redis-cli ping

# Check backend with all services
curl http://localhost:8000/health
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history
```

## Docker Compose Commands

### Development Environment

```bash
# Start all services (PostgreSQL + Backend + Redis + Weaviate)
docker-compose up -d

# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f weaviate
docker-compose logs -f redis

# Check service status
docker-compose ps

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose down -v
```

### Production Environment

```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production services
docker-compose -f docker-compose.prod.yml down
```

### Using Make Commands (Convenience)

```bash
# Development
make dev          # Start development environment
make dev-build    # Build and start development environment
make dev-down     # Stop development environment
make dev-logs     # Show development logs
make dev-shell    # Open shell in backend container

# Production
make prod         # Start production environment
make prod-build   # Build and start production environment
make prod-down    # Stop production environment
make prod-logs    # Show production logs

# Database operations
make migrate      # Run database migrations
make migrate-new  # Create new migration
make db-shell     # Open PostgreSQL shell

# Utilities
make test         # Run tests
make clean        # Clean up containers and volumes
make logs         # Show logs for all services

# Code Quality (Ruff)
make lint         # Run Ruff linter and show issues
make lint-fix     # Run Ruff linter and auto-fix issues
make format       # Format code with Ruff
make format-check # Check code formatting without changes
make quality      # Run both linting and formatting checks
```

### Service Management

```bash
# Check service status
docker-compose ps

# Restart specific service
docker-compose restart backend

# Scale services (if needed)
docker-compose up -d --scale backend=2

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec postgres psql -U attreq_user -d attreq_db
```

## Code Quality with Ruff

This project uses **Ruff** - an extremely fast Python linter and formatter written in Rust. Ruff replaces multiple tools (Black, isort, Flake8, etc.) with a single, unified tool.

### Quick Commands

```bash
# Check for linting issues
make lint

# Fix auto-fixable issues
make lint-fix

# Format code
make format

# Run all quality checks
make quality
```

### Configuration

Ruff is configured in `pyproject.toml` with:
- **Line length**: 100 characters
- **Target Python**: 3.11+
- **Enabled rules**: pycodestyle, Pyflakes, flake8-bugbear, isort, pyupgrade, and more
- **Auto-formatting**: Double quotes, 4-space indentation

### IDE Integration

The project includes VS Code settings in `.vscode/settings.json` that:
- Format code on save
- Auto-fix linting issues on save
- Organize imports automatically
- Show inline linting errors

For detailed Ruff usage, configuration, and best practices, see **[RUFF_GUIDE.md](RUFF_GUIDE.md)**.

## Development Workflow

1. **Make Changes**: Edit code in the `app/` directory
2. **Run Code Quality Checks**: Use `make quality` to lint and format
3. **Test Locally**: Use the interactive docs at `/docs`
4. **Run Migrations**: If models changed, create and apply migrations
5. **Test Endpoints**: Use curl or Postman to test API endpoints
6. **Commit Changes**: Follow conventional commit messages

## Security Features

- **Password Hashing**: bcrypt with 12 rounds
- **JWT Tokens**: Secure token-based authentication
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Environment Variables**: Sensitive data stored in environment variables

## Future Phases

### Phase 2: Google OAuth Integration
- Google OAuth2 authentication
- Social login endpoints
- OAuth user management

### Phase 3: AI/ML Pipeline
- Roboflow clothing detection
- Background removal with rembg
- Weaviate vector database integration
- Recommendation algorithm

### Phase 4: Wardrobe Management
- Clothing item upload and management
- Outfit creation and storage
- Style DNA analysis

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL container is running: `docker ps`
   - Check database credentials in `.env`
   - Verify database URL format

2. **Import Errors**
   - Ensure virtual environment is activated
   - Check Python path and module imports
   - Verify all dependencies are installed

3. **Migration Errors**
   - Check Alembic configuration
   - Ensure database is accessible
   - Verify model imports in `alembic/env.py`

4. **Authentication Errors**
   - Check JWT secret key is set
   - Verify token expiration settings
   - Ensure proper token format in requests

### Logs and Debugging

```bash
# View PostgreSQL logs
docker logs attreq_postgres_dev

# View application logs
# Logs are displayed in the terminal when running uvicorn

# Enable debug mode
export APP_DEBUG=true
```

## Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Write docstrings for all public functions
4. Test all endpoints before committing
5. Update this README for any new features

## License

This project is part of the ATTREQ fashion technology platform.
