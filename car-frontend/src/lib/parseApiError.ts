import { AxiosError } from 'axios';

// L7: Shared error parser so LoginForm and SignUpForm handle FastAPI validation
// errors (array of {msg}) and plain string details identically.
export function parseApiError(err: unknown, fallback: string): string {
  const axiosErr = err as AxiosError<{ detail: string | { msg: string }[] }>;
  const detail = axiosErr.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg).join(', ');
  }
  return (detail as string | undefined) ?? fallback;
}
