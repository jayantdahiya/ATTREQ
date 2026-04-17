# Frontend Implementation - Next.js PWA

## Setup

```bash
cd ~/projects/styleai
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu axios zustand
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card dialog input label
```

## PWA Configuration

### next.config.js
```javascript
/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development'
})

module.exports = withPWA({
  reactStrictMode: true,
})
```

### public/manifest.json
```json
{
  "name": "StyleAI",
  "short_name": "StyleAI",
  "description": "AI-powered wardrobe management",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### public/sw.js (Service Worker)
```javascript
const CACHE = 'styleai-v1';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => 
      cache.addAll(['/', '/dashboard', '/wardrobe'])
    )
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => 
      response || fetch(event.request)
    )
  );
});
```

## API Client

### lib/api.ts
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const auth = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', data),
};

export const wardrobe = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/wardrobe/upload', formData);
  },
  getItems: () => api.get('/wardrobe/items'),
};

export const outfits = {
  getDaily: (date: string) => api.get(`/outfits/daily?date=${date}`),
};

export default api;
```

## Pages

### app/page.tsx (Landing)
```typescript
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-6xl font-bold mb-8">StyleAI</h1>
      <p className="text-xl mb-8">Your AI-Powered Personal Stylist</p>
      <div className="flex gap-4">
        <Link href="/auth/login">
          <Button>Login</Button>
        </Link>
        <Link href="/auth/register">
          <Button variant="outline">Sign Up</Button>
        </Link>
      </div>
    </main>
  );
}
```

### app/dashboard/page.tsx
```typescript
'use client';

import { useEffect, useState } from 'react';
import { outfits } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [dailyOutfits, setDailyOutfits] = useState([]);

  useEffect(() => {
    loadOutfits();
  }, []);

  const loadOutfits = async () => {
    const today = new Date().toISOString().split('T')[0];
    const res = await outfits.getDaily(today);
    setDailyOutfits(res.data);
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-6">Today's Suggestions</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {dailyOutfits.map((outfit, idx) => (
          <Card key={idx} className="p-6">
            <h3 className="font-semibold mb-4">Outfit {idx + 1}</h3>
            {/* Render outfit images */}
            <Button className="w-full mt-4">Wear This</Button>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### app/wardrobe/page.tsx
```typescript
'use client';

import { useState } from 'react';
import { wardrobe } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function Wardrobe() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await wardrobe.upload(file);
      alert('Uploaded!');
    } catch (err) {
      alert('Failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-6">My Wardrobe</h1>
      <div className="mb-8">
        <Input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <Button onClick={handleUpload} disabled={!file || uploading} className="mt-4">
          {uploading ? 'Uploading...' : 'Upload Item'}
        </Button>
      </div>
    </div>
  );
}
```

## Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

**Estimated Time**: 2-3 weeks
