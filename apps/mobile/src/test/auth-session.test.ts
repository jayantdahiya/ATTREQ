import type { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { apiClient } from '@/lib/api/client';
import { registerSessionHandlers } from '@/lib/api/session';

describe('apiClient 401 refresh interceptor', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('refreshes once on 401 and retries the original request with the new token', async () => {
    let token = 'old-token';
    const refresh = jest.fn(async () => {
      token = 'new-token';
      return true;
    });
    const signOut = jest.fn(async () => undefined);
    registerSessionHandlers({ getAccessToken: () => token, refreshSession: refresh, signOut });

    const seenAuth: (string | undefined)[] = [];
    let calls = 0;
    apiClient.defaults.adapter = (async (config: InternalAxiosRequestConfig) => {
      calls += 1;
      seenAuth.push(config.headers?.Authorization as string | undefined);
      if (calls === 1) {
        const err = new Error('unauthorized') as AxiosError;
        err.isAxiosError = true;
        err.config = config;
        err.response = { status: 401, data: {}, statusText: 'Unauthorized', headers: {}, config };
        throw err;
      }
      return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config };
    }) as never;

    const res = await apiClient.get('/protected');

    expect(res.data).toEqual({ ok: true });
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(signOut).not.toHaveBeenCalled();
    expect(calls).toBe(2);
    expect(seenAuth[0]).toBe('Bearer old-token');
    expect(seenAuth[1]).toBe('Bearer new-token');
  });

  it('signs out when the refresh fails', async () => {
    const refresh = jest.fn(async () => false);
    const signOut = jest.fn(async () => undefined);
    registerSessionHandlers({ getAccessToken: () => 'stale', refreshSession: refresh, signOut });

    apiClient.defaults.adapter = (async (config: InternalAxiosRequestConfig) => {
      const err = new Error('unauthorized') as AxiosError;
      err.isAxiosError = true;
      err.config = config;
      err.response = { status: 401, data: {}, statusText: 'Unauthorized', headers: {}, config };
      throw err;
    }) as never;

    await expect(apiClient.get('/protected')).rejects.toBeTruthy();
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(signOut).toHaveBeenCalledTimes(1);
  });

  it('does not attempt refresh for the login endpoint', async () => {
    const refresh = jest.fn(async () => true);
    registerSessionHandlers({ getAccessToken: () => null, refreshSession: refresh, signOut: jest.fn() });

    apiClient.defaults.adapter = (async (config: InternalAxiosRequestConfig) => {
      const err = new Error('unauthorized') as AxiosError;
      err.isAxiosError = true;
      err.config = config;
      err.response = { status: 401, data: {}, statusText: 'Unauthorized', headers: {}, config };
      throw err;
    }) as never;

    await expect(apiClient.post('/auth/login', 'x')).rejects.toBeTruthy();
    expect(refresh).not.toHaveBeenCalled();
  });
});
