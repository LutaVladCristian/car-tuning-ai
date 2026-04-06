import { createContext, useContext, useState, type ReactNode } from 'react';
import { loginUser, registerUser } from '../api/auth';
import type { AuthUser, LoginRequest, RegisterRequest } from '../types/auth';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  register: (data: RegisterRequest) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const token = localStorage.getItem('car_tuning_token');
    const username = localStorage.getItem('car_tuning_username');
    if (token && username) return { token, username };
    return null;
  });

  const login = async (credentials: LoginRequest) => {
    const data = await loginUser(credentials);
    localStorage.setItem('car_tuning_token', data.access_token);
    localStorage.setItem('car_tuning_username', credentials.username);
    setUser({ token: data.access_token, username: credentials.username });
  };

  const logout = () => {
    localStorage.removeItem('car_tuning_token');
    localStorage.removeItem('car_tuning_username');
    setUser(null);
  };

  const register = async (data: RegisterRequest) => {
    await registerUser(data);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
