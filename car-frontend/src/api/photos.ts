import { apiClient } from './client';
import type { PhotoListResponse } from '../types/photo';

export async function listPhotos(skip = 0, limit = 20): Promise<PhotoListResponse> {
  const res = await apiClient.get<PhotoListResponse>('/photos', {
    params: { skip, limit },
  });
  return res.data;
}

export async function getPhotoUrl(id: number): Promise<string> {
  const res = await apiClient.get(`/photos/${id}`, { responseType: 'blob' });
  return URL.createObjectURL(res.data as Blob);
}

export async function getOriginalPhotoUrl(id: number): Promise<string> {
  const res = await apiClient.get(`/photos/${id}/original`, { responseType: 'blob' });
  return URL.createObjectURL(res.data as Blob);
}

export async function getRawMaskUrl(id: number): Promise<string> {
  const res = await apiClient.get(`/photos/${id}/mask/raw`, { responseType: 'blob' });
  return URL.createObjectURL(res.data as Blob);
}

export async function getEditMaskUrl(id: number): Promise<string> {
  const res = await apiClient.get(`/photos/${id}/mask/edit`, { responseType: 'blob' });
  return URL.createObjectURL(res.data as Blob);
}

export async function getPhotoBlob(id: number): Promise<Blob> {
  const res = await apiClient.get(`/photos/${id}`, { responseType: 'blob' });
  return res.data as Blob;
}
