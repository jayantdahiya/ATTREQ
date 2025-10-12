# Backend Implementation - FastAPI

## Quick Setup

```bash
cd ~/projects/styleai
mkdir -p backend/app/{api/v1/endpoints,core,crud,models,schemas,services,workers}
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy asyncpg alembic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart httpx Pillow rembg==2.0.55 weaviate-client redis
```

## Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── api/v1/endpoints/  (auth.py, users.py, wardrobe.py, outfits.py)
│   ├── core/              (config.py, security.py, database.py)
│   ├── crud/              (user.py, wardrobe.py, outfit.py)
│   ├── models/            (user.py, wardrobe.py, outfit.py)
│   ├── schemas/           (user.py, wardrobe.py, token.py)
│   ├── services/          (ai/, recommendation/, external/)
│   └── workers/           (image_processor.py)
├── Dockerfile
├── requirements.txt
└── .env
```

## Core Files

### app/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### app/core/config.py
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "StyleAI"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    DATABASE_URL: str
    WEAVIATE_HOST: str = "weaviate"
    REDIS_HOST: str = "redis"
    REDIS_PASSWORD: str
    ROBOFLOW_API_KEY: str
    OPENWEATHER_API_KEY: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### app/core/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/core/security.py
```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
```

## Database Models

### app/models/user.py
```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    location = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    wardrobe_items = relationship("WardrobeItem", back_populates="user")
    outfits = relationship("Outfit", back_populates="user")
```

### app/models/wardrobe.py
```python
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    original_image_url = Column(String, nullable=False)
    processed_image_url = Column(String)
    category = Column(String)
    color = Column(String)
    pattern = Column(String)
    season = Column(ARRAY(String))
    detection_confidence = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wardrobe_items")
```

## API Endpoints

### app/api/v1/endpoints/auth.py
```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import user as crud_user
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.core.security import create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud_user.create(db, obj_in=user_in)

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(deps.get_db)):
    user = crud_user.authenticate(db, email=form.username, password=form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer"
    }
```

### app/api/v1/endpoints/wardrobe.py
```python
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.models.user import User
from app.services.storage.file_handler import save_upload_file
from app.workers.image_processor import process_wardrobe_image

router = APIRouter()

@router.post("/upload")
async def upload_item(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    file_path = await save_upload_file(file, current_user.id, "originals")
    # Create DB entry and queue background processing
    background_tasks.add_task(process_wardrobe_image, file_path, current_user.id, db)
    return {"status": "processing", "file": file_path}

@router.get("/items")
def get_items(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # Return user's wardrobe items
    pass
```

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Database Migrations

```bash
# Initialize Alembic
cd backend
alembic init alembic

# Edit alembic/env.py to import models
# Create first migration
alembic revision --autogenerate -m "Initial tables"

# Apply migrations
alembic upgrade head
```

**Estimated Time**: 2 weeks
