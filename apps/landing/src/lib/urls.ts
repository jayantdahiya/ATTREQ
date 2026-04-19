const DEFAULT_LOGIN_URL = 'http://localhost:3000/auth/login';

export const appLoginUrl =
  process.env.NEXT_PUBLIC_APP_LOGIN_URL && process.env.NEXT_PUBLIC_APP_LOGIN_URL.trim().length > 0
    ? process.env.NEXT_PUBLIC_APP_LOGIN_URL
    : DEFAULT_LOGIN_URL;
