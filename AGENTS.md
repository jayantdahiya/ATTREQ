# AGENTS.md

## Project Overview

ATTREQ is an AI-powered personal stylist Progressive Web App (PWA) that eliminates daily outfit decision fatigue. The application combines FastAPI backend with Next.js frontend to provide intelligent wardrobe management and personalized outfit recommendations based on weather, occasion, and user preferences.

**Tech Stack:**
- **Backend**: FastAPI 0.119.0, Python 3.11+, PostgreSQL 15, Redis 7, Weaviate vector DB
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Zustand
- **AI/ML**: Roboflow API, rembg, scikit-learn, Weaviate text2vec-transformers
- **Infrastructure**: Docker Compose, Alembic migrations

**Key Features:**
- AI-powered clothing recognition and tagging
- Weather-based outfit recommendations
- Vector search for compatible clothing items
- Outfit tracking and user preference learning
- Background removal and thumbnail generation

## Setup Commands

### Backend (Docker Compose)

```bash
# Navigate to backend directory
cd App/Backend

# Copy environment template
cp .env.example .env

# Start all backend services (PostgreSQL, Redis, Weaviate, Backend)
docker-compose up -d --build

# Run database migrations
docker exec attreq_backend alembic upgrade head

# View backend logs
docker-compose logs -f backend

# Quick start (build + migrate)
make start
```

### Frontend (npm)

```bash
# Navigate to frontend directory
cd App/Frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Database Migrations

```bash
# Create new migration
docker exec attreq_backend alembic revision --autogenerate -m "description"

# Apply migrations
docker exec attreq_backend alembic upgrade head

# Rollback migration
docker exec attreq_backend alembic downgrade -1
```

## Code Style

### Backend (Python)

- **Linter**: Follow Ruff configuration in `pyproject.toml`
- **Line length**: 100 characters maximum
- **Quotes**: Use double quotes for strings
- **Type hints**: Required for all functions
- **Docstrings**: Required for public functions
- **Imports**: Use isort via Ruff (app modules as first-party)
- **Quality checks**: Run `make quality` before committing

```bash
# Run code quality checks
make quality

# Auto-fix linting issues
make lint-fix

# Format code
make format
```

### Frontend (TypeScript)

- **TypeScript**: Strict mode enabled
- **Linting**: Follow existing ESLint configuration
- **Components**: Use functional components with hooks
- **State**: Zustand for state management
- **UI**: shadcn/ui components
- **Styling**: Tailwind CSS classes

## Architecture

### Backend Structure (`App/Backend/`)
```
app/
├── api/v1/endpoints/     # API route handlers
├── core/               # Configuration & security
├── crud/               # Database operations
├── models/             # SQLAlchemy database models
├── schemas/            # Pydantic request/response schemas
└── services/           # Business logic
    ├── ai/             # AI/ML services
    ├── cache/          # Redis caching
    ├── external/       # External API integrations
    ├── recommendation/ # Recommendation algorithms
    └── storage/        # File storage
```

### Frontend Structure (`App/Frontend/`)
```
app/                    # Next.js App Router pages
components/             # React components
├── ui/                # shadcn/ui components
lib/                   # Utility libraries
├── api/               # API client functions
store/                 # Zustand stores
```

### Database Architecture
- **PostgreSQL**: Primary database for users, wardrobe items, outfits
- **Weaviate**: Vector database for semantic clothing search
- **Redis**: Caching for weather data (1h) and recommendations (24h)

## Development Workflow

### Making Changes

1. **Backend changes**: Edit code in `App/Backend/app/` directory
2. **Code quality**: Run `make quality` for linting and formatting
3. **Testing**: Use interactive API docs at http://localhost:8000/docs
4. **Migrations**: If models changed, create and apply migrations
5. **Frontend changes**: Ensure backend is running, start `npm run dev`

### Key Directories

- `App/Backend/app/api/v1/endpoints/` - API route handlers
- `App/Backend/app/services/` - Business logic (AI, cache, external APIs, recommendations, storage)
- `App/Backend/app/models/` - SQLAlchemy database models
- `App/Backend/app/schemas/` - Pydantic request/response schemas
- `App/Frontend/app/` - Next.js pages and layouts
- `App/Frontend/components/` - React components
- `App/Frontend/lib/api/` - API client functions

## Testing Instructions

### Backend Testing
- **Current status**: No formal test suite (Phase 5 in progress)
- **Manual testing**: Use interactive API docs at `/docs`
- **Test scripts**: `./scripts/test_recommendations.sh`, `./scripts/test_wardrobe_api.sh`
- **Health check**: `curl http://localhost:8000/health`

### Frontend Testing
- **Development**: Run `npm run dev` and test in browser
- **Current status**: No formal test suite
- **Type checking**: `npm run type-check` (if available)

## Environment Configuration

### Backend `.env` Requirements
```bash
# Database
DATABASE_URL=postgresql+asyncpg://attreq_user:password@postgres:5432/attreq_db
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

### Frontend `.env.local` Requirements
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_UPLOADS_URL=http://localhost:8000/uploads
NEXT_PUBLIC_APP_NAME=ATTREQ
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Key Services & Integrations

### AI Services
- **Roboflow API**: Clothing detection and categorization
- **rembg**: Automatic background removal
- **scikit-learn**: Recommendation algorithms and scoring

### Vector Search
- **Weaviate**: Semantic search for compatible clothing items
- **text2vec-transformers**: Sentence transformers for embeddings

### Caching
- **Redis**: Weather data (1h TTL), recommendations (24h TTL)
- **Performance**: High-speed caching for API responses

### External APIs
- **OpenWeatherMap**: Real-time weather data for outfit suggestions
- **File Storage**: Local uploads with organized directory structure

## Security & Best Practices

- **Authentication**: JWT tokens with refresh token rotation
- **Password Security**: bcrypt hashing with 12 rounds
- **Input Validation**: Pydantic schema validation on all endpoints
- **CORS Protection**: Configurable cross-origin resource sharing
- **SQL Injection**: SQLAlchemy ORM prevents SQL injection
- **File Upload**: Size limits and type validation
- **Environment Variables**: Sensitive data stored securely

## Common Issues & Troubleshooting

### Database Connection
- **Issue**: Database connection errors
- **Solution**: Ensure containers running via `docker ps`
- **Check**: Database credentials in `.env` file

### Redis Connection
- **Issue**: Redis connection failed
- **Solution**: Check `docker-compose ps` for Redis service
- **Verify**: Redis settings in `.env`

### Weather API Errors
- **Issue**: No weather data for recommendations
- **Solution**: Verify `OPENWEATHER_API_KEY` in `.env`
- **Test**: API key validity at OpenWeatherMap

### No Recommendations Generated
- **Issue**: Empty recommendation responses
- **Solution**: Ensure minimum 2 wardrobe items uploaded
- **Check**: Item processing status and occasion types

### Service Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f weaviate
docker-compose logs -f redis
```

## Important Notes

- **Always use docker-compose** for backend services (PostgreSQL, Redis, Weaviate, Backend)
- **Run migrations via docker exec** into backend container: `docker exec attreq_backend alembic upgrade head`
- **Frontend is standalone** npm project - can run independently
- **Weaviate and Redis must be running** for full AI functionality
- **Phase 5 (testing/deployment)** currently in progress
- **File uploads** stored in organized directory structure: `uploads/originals/`, `uploads/processed/`, `uploads/thumbnails/`

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Weaviate**: http://localhost:8080
- **Redis**: localhost:6379

## Codebase Knowledge Graph (codebase-memory-mcp)

This project is indexed in `codebase-memory-mcp` as **`Users-Work-Desktop-Personal-Project Attreq`**. Always use this MCP for code discovery before falling back to Grep/Glob/Read.

### Project Identifier

All MCP calls require the `project` parameter:
```
"project": "Users-Work-Desktop-Personal-Project Attreq"
```

### Mandatory Workflow

1. **Finding functions, classes, routes, variables** -> use `search_graph` (not Grep/Glob)
2. **Reading source code** -> use `search_graph` to find `qualified_name`, then `get_code_snippet`
3. **Tracing call chains / impact analysis** -> use `trace_call_path` (not grep for function names)
4. **Architecture overview** -> use `get_architecture`
5. **Complex multi-hop queries** -> use `query_graph` with Cypher
6. **Text pattern search with graph enrichment** -> use `search_code`

### Tool Reference

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `index_repository` | Re-index after major changes | `repo_path`, `mode` (full/fast) |
| `index_status` | Check if index is current | `project` |
| `list_projects` | List all indexed projects | (none) |
| `get_architecture` | High-level project overview | `project`, `aspects` (array, use `["all"]`) |
| `get_graph_schema` | Node labels, edge types | `project` |
| `search_graph` | Find functions/classes/routes/variables | `project`, `label`, `name_pattern`, `file_pattern`, `min_degree`, `limit` |
| `get_code_snippet` | Read source for a symbol | `qualified_name` (from search_graph), `project`, `include_neighbors` |
| `search_code` | Grep + graph enrichment | `pattern`, `project`, `mode` (compact/full/files), `file_pattern`, `limit` |
| `trace_call_path` | Who calls / what calls | `function_name`, `project`, `direction` (inbound/outbound/both), `depth` |
| `query_graph` | Raw Cypher queries | `query`, `project`, `max_rows` |
| `detect_changes` | Git diff impact analysis | `project`, `scope`, `depth`, `base_branch` |
| `manage_adr` | Architecture Decision Records | `project`, `mode` (get/update/sections), `content` |
| `ingest_traces` | Add runtime traces to graph | `traces` (array of objects), `project` |
| `delete_project` | Remove project from index | `project` |

### Graph Schema (Current)

**Node Labels**: Section (1014), Variable (205), Function (176), File (152), Module (152), Method (106), Class (80), Folder (44), Route (24), Interface (20), Type (3), Project (1)

**Edge Types**: DEFINES, CALLS, USAGE, CONTAINS_FILE, DEFINES_METHOD, CONTAINS_FOLDER, HANDLES, DECORATES, WRITES, TESTS

### Common Patterns

**Find all API routes:**
```
search_graph(project=..., label="Route")
```

**Find a class and read its source:**
```
search_graph(project=..., label="Class", name_pattern="BackgroundRemovalService")
-> get qualified_name from result
get_code_snippet(project=..., qualified_name="...", include_neighbors=true)
```

**Trace who calls a function (3 hops):**
```
trace_call_path(project=..., function_name="remove_background", direction="both", depth=3)
```

**Cypher - list functions with most callers:**
```
query_graph(project=..., query="MATCH (f:Function) RETURN f.name, f.file_path ORDER BY f.name LIMIT 10")
```

**Find high-degree nodes (most connected, potential refactor targets):**
```
search_graph(project=..., label="Function", min_degree=5)
```

### Re-indexing

Run `index_repository` with `mode: "full"` after significant structural changes (new files, renamed modules, deleted code). Use `mode: "fast"` for incremental updates.

### ADR (Architecture Decision Record)

An ADR is stored in the graph. Use `manage_adr(mode="get")` to read it, `manage_adr(mode="update", content="...")` to update it. Keep it current when architectural decisions change.

---

## Raspberry Pi Deployment Context (Updated 2026-04-01)

- **Pi host**: `jayant@192.168.29.27`
- **Backend local path**: `App/Backend`
- **Backend remote path**: `/home/jayant/workspaces/attreq-backend`
- **Deployment tool**: `pi-dev` (`doctor -> sync -> compose`)
- **Pi runtime**: Docker Compose with `docker-compose.prod.yml`
- **Current Pi backend health (LAN)**: `http://192.168.29.27:8000/health` -> `200 OK`
- **Cloudflare Tunnel public URL**: `https://dev-home-pi.online/`
- **Tunnel ingress target**: `http://localhost:8000` on Pi (configured in Cloudflare Zero Trust)
- **Cloudflare health URL**: `https://dev-home-pi.online/health` -> `200 OK`
- **Important env for production host validation**:
  `TRUSTED_HOSTS=["attreq.com","*.attreq.com","localhost","127.0.0.1","192.168.29.27","dev-home-pi.online","*.dev-home-pi.online"]`
- **Known behavior**:
  - If the public URL returns `400 Invalid host header`, add hostname to `TRUSTED_HOSTS`.
  - If the public URL returns `502` right after deploy, wait for backend startup to complete and recheck health.
  - Production compose currently runs `postgres`, `redis`, and `backend`; `weaviate` is not in `docker-compose.prod.yml`.
