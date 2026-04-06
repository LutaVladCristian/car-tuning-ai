import { apiClient } from './client';
import type { RegisterRequest, RegisterResponse, LoginRequest, TokenResponse } from '../types/auth';

export async function registerUser(data: RegisterRequest): Promise<RegisterResponse> {
  const res = await apiClient.post<RegisterResponse>('/auth/register', data);
  return res.data;
}

export async function loginUser(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/login', data);
  return res.data;
}
