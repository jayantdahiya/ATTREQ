# Development Workflow

## Daily Routine

### Morning
```bash
# SSH to Pi
ssh styleai-pi

# Check services
cd ~/projects/styleai
docker compose ps

# View logs
docker compose logs --tail=50 -f
```

### Development with Cursor

1. Open project in Cursor:
```bash
cursor ~/projects/styleai
```

2. Create `.cursorrules`:
```
You are building StyleAI, a FastAPI + Next.js PWA for wardrobe management.

Stack:
- Backend: Python 3.11, FastAPI, SQLAlchemy, Weaviate
- Frontend: Next.js 15, TypeScript, Tailwind, Shadcn/UI
- Database: PostgreSQL + Weaviate + Redis
- Hosting: Self-hosted Raspberry Pi 5

Guidelines:
- Use async/await for API calls
- Add type hints to Python functions
- Write Pydantic schemas for validation
- Use Shadcn components for UI
- Follow REST API conventions
```

3. AI-Assisted Development:
- `Cmd+K`: Inline code edits
- `Cmd+L`: Chat with AI
- `Cmd+Shift+L`: Multi-file edits (Composer)

### Testing Before Commit
```bash
# Backend
cd backend
source venv/bin/activate
pytest
black app/
flake8 app/

# Frontend
cd frontend
npm run type-check
npm run lint
```

### Commit & Deploy
```bash
git add .
git commit -m "feat: add outfit generation"
git push origin main

# Auto-deploys via GitHub Actions
```

## Debugging

### Backend Logs
```bash
docker compose logs -f backend
docker exec -it styleai_backend bash
```

### Database Inspection
```bash
# PostgreSQL
docker exec -it styleai_postgres psql -U styleai_user -d styleai

# Weaviate
curl http://localhost:8080/v1/schema
```

### Performance Monitoring
```bash
~/monitor-styleai.sh
```

## Git Workflow
- `main`: Production
- `develop`: Integration
- `feat/*`: Feature branches

## Cursor Shortcuts
- `Cmd+K`: Edit code
- `Cmd+L`: Chat
- `Cmd+I`: Accept suggestion

**Time**: ~25-30 hrs/week for 10 weeks
