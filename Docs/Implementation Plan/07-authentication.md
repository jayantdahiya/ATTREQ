# Authentication System

## JWT Flow

1. User logs in → Backend generates access + refresh tokens
2. Access token (15min) stored in localStorage
3. Refresh token (7 days) in HttpOnly cookie
4. Include access token in API requests
5. On 401, refresh access token automatically

## Backend Implementation

### Token Generation
```python
from datetime import datetime, timedelta
from jose import jwt

def create_tokens(user_id: str):
    access_exp = datetime.utcnow() + timedelta(minutes=15)
    refresh_exp = datetime.utcnow() + timedelta(days=7)

    access_token = jwt.encode(
        {"sub": user_id, "exp": access_exp, "type": "access"},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    refresh_token = jwt.encode(
        {"sub": user_id, "exp": refresh_exp, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    return {"access_token": access_token, "refresh_token": refresh_token}
```

### Token Validation
```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
    except:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
```

## Frontend Implementation

### Login Component
```typescript
'use client';

import { useState } from 'react';
import { auth } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await auth.login({ username: email, password });
      localStorage.setItem('access_token', res.data.access_token);
      router.push('/dashboard');
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Login</button>
    </form>
  );
}
```

### Token Refresh Interceptor
```typescript
import axios from 'axios';

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        const res = await axios.post('/api/auth/refresh');
        localStorage.setItem('access_token', res.data.access_token);
        error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
        return axios(error.config);
      } catch {
        localStorage.clear();
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);
```

## Google OAuth (Optional)

### Backend
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    'google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get('/auth/google')
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)

@router.get('/auth/google/callback')
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token['userinfo']
    # Create/get user, return JWT tokens
```

**Estimated Time**: 3-4 days
