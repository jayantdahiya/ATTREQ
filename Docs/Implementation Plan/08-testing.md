# Testing Strategy

## Backend Tests (pytest)

### Setup
```bash
cd backend
pip install pytest pytest-asyncio httpx
```

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

### tests/conftest.py
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

@pytest.fixture(scope="session")
def test_db():
    engine = create_engine("postgresql://test:test@localhost/test")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

### tests/test_auth.py
```python
from app.crud import user as crud_user
from app.schemas.user import UserCreate

def test_create_user(db_session):
    user_in = UserCreate(email="test@test.com", password="Test123!")
    user = crud_user.create(db_session, obj_in=user_in)
    assert user.email == "test@test.com"
    assert user.password_hash is not None

def test_authenticate(db_session):
    user_in = UserCreate(email="auth@test.com", password="Pass123!")
    user = crud_user.create(db_session, obj_in=user_in)
    auth_user = crud_user.authenticate(db_session, email="auth@test.com", password="Pass123!")
    assert auth_user is not None
```

## Frontend E2E Tests (Playwright)

### Setup
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

### playwright.config.ts
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:3000',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
  },
});
```

### tests/login.spec.ts
```typescript
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('input[type="email"]', 'test@example.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

### tests/upload.spec.ts
```typescript
import { test, expect } from '@playwright/test';

test('upload wardrobe item', async ({ page }) => {
  await page.goto('/wardrobe');
  await page.setInputFiles('input[type="file"]', 'test-images/shirt.jpg');
  await page.click('button:has-text("Upload")');
  await expect(page.locator('text=Uploaded')).toBeVisible();
});
```

## Run Tests
```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npx playwright test
npx playwright test --ui  # Interactive mode
```

**Estimated Time**: 1 week
