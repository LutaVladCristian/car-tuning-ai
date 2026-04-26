import { createContext } from 'react';
import type { AuthUser } from '../types/auth';

export interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
