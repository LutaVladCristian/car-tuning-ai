import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ReactNode } from 'react';

// Firebase must be mocked before AuthProvider is imported to prevent
// getAuth() from trying to validate a real API key in the test environment.
vi.mock('../lib/firebase', () => ({
  auth: {},
  googleProvider: {},
}));

// vi.hoisted ensures these are initialized before vi.mock hoisting runs.
const { mockOnAuthStateChanged, mockSignInWithPopup, mockSignOut } = vi.hoisted(() => ({
  mockOnAuthStateChanged: vi.fn(),
  mockSignInWithPopup: vi.fn(),
  mockSignOut: vi.fn(),
}));

vi.mock('firebase/auth', () => ({
  onAuthStateChanged: mockOnAuthStateChanged,
  signInWithPopup: mockSignInWithPopup,
  signOut: mockSignOut,
}));

vi.mock('../api/auth', () => ({
  syncFirebaseUser: vi.fn(),
}));

import { AuthProvider } from './AuthContext';
import { useAuth } from './useAuth';
import { syncFirebaseUser } from '../api/auth';

const mockSyncFirebaseUser = vi.mocked(syncFirebaseUser);

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

beforeEach(() => {
  vi.clearAllMocks();
  // Default: fire onAuthStateChanged immediately with no user so loading resolves.
  mockOnAuthStateChanged.mockImplementation((_auth: unknown, callback: (u: null) => void) => {
    callback(null);
    return vi.fn();
  });
});

describe('AuthContext', () => {
  it('initializes with null user when no Firebase user is signed in', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('sets user when Firebase reports a signed-in user', () => {
    const fakeUser = { uid: 'uid123', email: 'alice@example.com', displayName: 'Alice' };
    mockOnAuthStateChanged.mockImplementation((_auth: unknown, callback: (u: typeof fakeUser) => void) => {
      callback(fakeUser);
      return vi.fn();
    });

    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.user?.uid).toBe('uid123');
    expect(result.current.user?.email).toBe('alice@example.com');
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('calls signInWithPopup and syncFirebaseUser on login', async () => {
    const fakeIdToken = 'firebase-id-token';
    const fakeUser = {
      uid: 'uid123',
      email: 'a@b.com',
      displayName: 'A',
      getIdToken: vi.fn().mockResolvedValue(fakeIdToken),
    };
    mockSignInWithPopup.mockResolvedValueOnce({ user: fakeUser });
    mockSyncFirebaseUser.mockResolvedValueOnce({
      id: 1, firebase_uid: 'uid123', email: 'a@b.com', display_name: 'A',
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login();
    });

    expect(mockSignInWithPopup).toHaveBeenCalledTimes(1);
    expect(mockSyncFirebaseUser).toHaveBeenCalledWith(fakeIdToken);
  });

  it('calls signOut on logout', async () => {
    mockSignOut.mockResolvedValueOnce(undefined);
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });

  it('throws when useAuth is used outside of AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used within AuthProvider');
  });
});
