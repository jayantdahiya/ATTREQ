import { AxiosError } from 'axios';

/** Turns an API/network error into a single user-facing sentence. */
export function describeAuthError(error: unknown): string {
  const ax = error as AxiosError<{ detail?: unknown }> | undefined;
  if (ax && ax.isAxiosError) {
    if (!ax.response) return 'Network error. Check your connection and try again.';
    const detail = ax.response.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (ax.response.status === 401) return 'Incorrect email or password.';
    if (ax.response.status === 400) return 'That request could not be completed.';
    return `Something went wrong (${ax.response.status}).`;
  }
  if (error instanceof Error) return error.message;
  return 'Something went wrong.';
}
