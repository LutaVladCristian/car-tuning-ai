import { createContext } from 'react';
import type { AuthUser, LoginRequest, RegisterRequest } from '../types/auth';

export interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  register: (data: RegisterRequest) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
