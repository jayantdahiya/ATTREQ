# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Users (PWA Clients)                       │
│              Mobile/Desktop Browsers                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS (443)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Raspberry Pi 5 Host (8GB RAM)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Nginx Reverse Proxy (:80, :443)               │  │
│  │    (SSL/TLS, Load Balancing, Static Caching)          │  │
│  └──────────┬─────────────────────────┬──────────────────┘  │
│             │                         │                      │
│  ┌──────────▼──────────┐   ┌─────────▼──────────┐          │
│  │  Next.js Frontend   │   │   FastAPI Backend  │          │
│  │    (Port 3000)      │   │    (Port 8000)     │          │
│  │                     │   │                    │          │
│  │ • SSR/SSG          │   │ • REST API         │          │
│  │ • Service Worker   │   │ • WebSockets       │          │
│  │ • PWA Manifest     │   │ • Background Jobs  │          │
│  │ • Offline Cache    │   │ • Image Processing │          │
│  └─────────────────────┘   └─────┬──────────────┘          │
│                                   │                          │
│                       ┌───────────┼───────────┐             │
│                       │           │           │             │
│            ┌──────────▼─┐  ┌─────▼─────┐  ┌─▼─────────┐   │
│            │ PostgreSQL │  │ Weaviate  │  │   Redis   │   │
│            │   (:5432)  │  │  (:8080)  │  │  (:6379)  │   │
│            │            │  │           │  │           │   │
│            │ • User DB  │  │ • Vectors │  │ • Cache   │   │
│            │ • Wardrobe │  │ • Hybrid  │  │ • Queue   │   │
│            │ • Outfits  │  │   Search  │  │ • Session │   │
│            └────────────┘  └───────────┘  └───────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     Local File Storage (External SSD)                 │  │
│  │  /mnt/attreq/uploads/{originals,processed,thumbs}   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       │ External APIs (HTTPS)
                       │
           ┌───────────┼───────────┐
           │           │           │
    ┌──────▼──────┐ ┌──▼────────┐ ┌▼────────────┐
    │  Roboflow   │ │OpenWeather│ │   Google    │
    │  Detection  │ │    API    │ │ OAuth (opt) │
    │   API       │ │           │ │             │
    └─────────────┘ └────────────┘ └─────────────┘
```

## Component Details

### 1. Frontend Layer (Next.js 15 PWA)
**Technology**: Next.js 15+ App Router, React 18+, TypeScript 5.3+, Tailwind CSS

**Responsibilities**:
- Server-side rendering for SEO and performance
- Progressive Web App capabilities (installable, offline-first)
- Responsive UI with Shadcn/UI components
- Client-side state management (Zustand)
- Image optimization and lazy loading
- Service Worker for offline functionality

**Key Routes**:
- `/` - Landing page
- `/auth/login` - Authentication
- `/dashboard` - Daily outfit suggestions
- `/wardrobe` - Wardrobe management
- `/outfits/history` - Past outfits
- `/profile` - User settings

**Port**: 3000 (internal), exposed via Nginx reverse proxy on 443

---

### 2. Backend Layer (FastAPI)
**Technology**: Python 3.11+, FastAPI 0.109+, Uvicorn ASGI server

**Responsibilities**:
- RESTful API endpoints with OpenAPI documentation
- JWT-based authentication and authorization
- Business logic orchestration
- AI/ML pipeline coordination
- Background task processing (Celery alternative: FastAPI BackgroundTasks)
- File upload validation and storage
- WebSocket connections for real-time updates

**Core Modules**:
```
app/
├── api/v1/endpoints/    # Route handlers
├── core/                # Config, security, database
├── crud/                # Database operations
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic validation
├── services/            # Business logic
│   ├── ai/              # Roboflow, Rembg, embeddings
│   ├── recommendation/  # Outfit algorithm
│   └── external/        # Weather API
└── workers/             # Background jobs
```

**Port**: 8000 (internal), `/api` prefix via Nginx

---

### 3. Database Layer

#### PostgreSQL 15 (Relational Database)
**Purpose**: Primary data store for users, wardrobe items, outfits, preferences

**Key Tables**:
```sql
users (id, email, password_hash, location, preferences)
wardrobe_items (id, user_id, image_url, category, color, pattern, season, embedding)
outfits (id, user_id, date, item_ids, weather_data, event_type, user_rating)
style_profiles (id, user_id, style_tags, color_preferences, formality_score)
```

**Extensions**:
- `uuid-ossp` for UUID generation
- `pgvector` for vector similarity (backup to Weaviate)

#### Weaviate (Vector Database)
**Purpose**: Fast semantic search for clothing item recommendations

**Schema**:
```python
{
  "class": "ClothingItem",
  "vectorizer": "text2vec-transformers",
  "properties": ["itemId", "userId", "category", "color", "season", "description"]
}
```

**Use Cases**:
- Find visually similar items
- Hybrid search (keyword + semantic)
- Outfit compatibility scoring

#### Redis (Cache & Queue)
**Purpose**: Session storage, API caching, background job queue

**Key Patterns**:
- `session:{user_id}` - JWT refresh tokens
- `outfit:{user_id}:{date}` - Daily outfit cache (24h TTL)
- `queue:image-processing` - Upload processing queue

---

### 4. AI/ML Pipeline

#### Clothing Recognition (Roboflow API)
**Model**: Pre-trained fashion detection
**Input**: Processed clothing image (background removed)
**Output**: Category, color, pattern, confidence score
**Free Tier**: 1000 API calls/month

**Process**:
1. User uploads image
2. Remove background (Rembg)
3. Send to Roboflow API
4. Extract attributes
5. Store in PostgreSQL + Weaviate

#### Background Removal (Rembg)
**Library**: `rembg` with U2-Net model
**Processing**: Server-side on FastAPI
**Why**: Improves detection accuracy, consistent image quality

#### Recommendation Algorithm (Hybrid)
**Approach**: Content-based filtering + Collaborative signals

**Steps**:
1. Get user's wardrobe from database
2. Filter by weather (temperature, condition)
3. Filter by event type (manual dropdown: casual, meeting, party)
4. Use Weaviate to find compatible item combinations
5. Score outfits based on:
   - Color harmony
   - Formality matching
   - Season compatibility
   - User preferences (style profile)
   - Past outfit ratings
6. Return top 3 unique outfit suggestions

**Pseudocode**:
```python
def generate_outfits(user_id, weather, event_type):
    items = get_wardrobe(user_id)
    suitable = filter_by_weather(items, weather)

    base_item = select_base(suitable, event_type)  # bottom
    tops = weaviate_search(base_item, category='top')

    combinations = []
    for top in tops:
        score = calculate_compatibility(base_item, top)
        combinations.append((base_item, top, score))

    return sorted(combinations, key=lambda x: x[2])[:3]
```

---

### 5. External Integrations

#### OpenWeatherMap API
**Endpoint**: Current Weather API
**Data**: Temperature, condition, humidity
**Location Strategy**:
1. Request browser geolocation (lat/lon)
2. If denied, use city from user profile
3. Cache weather data for 1 hour (Redis)

#### Google OAuth2 (Optional)
**Purpose**: Alternative login method
**Scope**: `openid email profile` (minimal)
**Flow**: Authorization Code flow with PKCE

---

## Data Flow Examples

### User Registration Flow
```
1. User submits email + password
2. Frontend validates and sends POST /api/auth/register
3. Backend hashes password (bcrypt)
4. Create user record in PostgreSQL
5. Generate JWT access + refresh tokens
6. Return tokens to frontend
7. Store access token in localStorage
8. Redirect to onboarding (style preferences)
```

### Wardrobe Upload Flow
```
1. User selects image from device
2. Frontend validates file type/size
3. Upload via POST /api/wardrobe/upload (multipart)
4. Backend saves to /mnt/styleai/uploads/originals/
5. Create wardrobe_item record (status: processing)
6. Queue background job
7. Return item_id immediately

Background Job:
8. Load original image
9. Remove background with Rembg → save to /processed/
10. Call Roboflow API for detection
11. Generate thumbnail (300px)
12. Extract embedding and add to Weaviate
13. Update wardrobe_item with results
14. Notify frontend via WebSocket (optional)
```

### Daily Outfit Generation Flow
```
1. User opens app in morning
2. Frontend checks localStorage cache
3. If cache miss, call GET /api/outfits/daily?date=2025-10-11
4. Backend checks Redis cache
5. If Redis miss:
   a. Get user location from profile
   b. Call OpenWeather API
   c. Load user's wardrobe items
   d. Run recommendation algorithm with Weaviate
   e. Generate 3 outfit combinations
   f. Save to database
   g. Cache in Redis (24h TTL)
6. Return outfit objects with image URLs
7. Frontend renders carousel
8. User selects outfit → POST /api/outfits/{id}/wear
```

---

## Security Architecture

### Authentication Flow
**Token Types**:
- **Access Token**: 15-minute expiry, sent in Authorization header
- **Refresh Token**: 7-day expiry, stored in HttpOnly cookie (XSS protection)

**Request Flow**:
```
1. User logs in → Receive access + refresh tokens
2. Store access in localStorage
3. Include in header: Authorization: Bearer <access_token>
4. Backend validates JWT signature and expiry
5. When access expires (401 error):
   a. Frontend calls /api/auth/refresh with refresh token
   b. Backend validates refresh token
   c. Issue new access token
   d. Retry original request
```

### Data Protection
- **Passwords**: bcrypt hashing (12 rounds)
- **Database**: Not exposed externally, Unix socket only
- **Images**: User-isolated directories (/uploads/{user_id}/)
- **API**: Rate limiting (100 req/min per user via Redis)
- **HTTPS**: Let's Encrypt SSL certificates

---

## Performance Optimizations

### Caching Strategy
**Layer 1 - Browser (Service Worker)**:
- Static assets: 7-day cache
- API responses: Network-first with cache fallback

**Layer 2 - Redis**:
- Outfit suggestions: 24h TTL
- Weather data: 1h TTL
- User sessions: 7 days

**Layer 3 - Nginx**:
- Gzip compression
- Browser caching headers
- HTTP/2 multiplexing

### Database Optimization
- Indexes on: user_id, date, category columns
- Connection pooling: 10 connections
- Query optimization with EXPLAIN ANALYZE
- Weaviate HNSW index for fast similarity search

---

## Scalability Considerations

**Current MVP**: Single Raspberry Pi 5 (8GB RAM)

**Estimated Capacity**:
- 100-500 concurrent users
- 10,000 total users
- 1 million wardrobe items
- Response time <2s for outfit generation

**Future Scaling Path**:
1. Add second Raspberry Pi with load balancer
2. Separate database to dedicated server
3. Migrate to cloud (DigitalOcean/AWS) for global reach
4. Implement CDN for image delivery
5. Microservices architecture for AI pipeline

---

## Monitoring & Backup

### Backup Strategy
- **PostgreSQL**: Daily pg_dump to external HDD
- **Images**: Nightly rsync to USB drive
- **Weaviate**: Can rebuild from PostgreSQL data
- **Retention**: 7 days local, 30 days external

### Health Checks
- Docker healthchecks for all services
- Nginx logs to /mnt/attreq/logs/
- Manual monitoring via `htop` and `docker stats`
- Future: Prometheus + Grafana dashboard (V2)

---

**Next**: Proceed to `03-infrastructure.md` for Raspberry Pi setup.
