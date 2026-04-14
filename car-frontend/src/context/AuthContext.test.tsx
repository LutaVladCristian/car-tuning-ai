import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider } from './AuthContext';
import { useAuth } from './useAuth';

vi.mock('../api/auth', () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
}));

import { loginUser, registerUser } from '../api/auth';

const mockLoginUser = vi.mocked(loginUser);
const mockRegisterUser = vi.mocked(registerUser);

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

describe('AuthContext', () => {
  it('initializes with null user when localStorage is empty', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('restores user from localStorage on mount', () => {
    localStorage.setItem('car_tuning_token', 'tok123');
    localStorage.setItem('car_tuning_username', 'alice');

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user?.username).toBe('alice');
    expect(result.current.user?.token).toBe('tok123');
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('stores token and username in localStorage after login', async () => {
    mockLoginUser.mockResolvedValueOnce({ access_token: 'jwt-abc', token_type: 'bearer' });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ username: 'bob', password: 'pass' });
    });

    expect(localStorage.getItem('car_tuning_token')).toBe('jwt-abc');
    expect(localStorage.getItem('car_tuning_username')).toBe('bob');
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.username).toBe('bob');
  });

  it('clears localStorage and nulls user on logout', async () => {
    localStorage.setItem('car_tuning_token', 'tok123');
    localStorage.setItem('car_tuning_username', 'alice');

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('car_tuning_token')).toBeNull();
    expect(localStorage.getItem('car_tuning_username')).toBeNull();
  });

  it('calls registerUser with the correct payload', async () => {
    mockRegisterUser.mockResolvedValueOnce({ id: 1, username: 'carol', email: 'carol@example.com' });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.register({ username: 'carol', email: 'carol@example.com', password: 'pass' });
    });

    expect(mockRegisterUser).toHaveBeenCalledWith({
      username: 'carol',
      email: 'carol@example.com',
      password: 'pass',
    });
  });

  it('throws when useAuth is used outside of AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used within AuthProvider');
  });
});
