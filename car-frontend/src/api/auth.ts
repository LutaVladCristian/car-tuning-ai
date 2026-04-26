import { apiClient } from './client';
import type { UserResponse } from '../types/auth';

export async function syncFirebaseUser(idToken: string): Promise<UserResponse> {
  const res = await apiClient.post<UserResponse>('/auth/firebase', { id_token: idToken });
  return res.data;
}
