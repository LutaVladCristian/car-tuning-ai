import { apiClient } from './client';

export interface PreviewResponse {
  photo_id: number;
}

export async function previewPhoto(
  file: File | Blob,
  prompt: string,
  editCar: boolean,
  size = 'auto'
): Promise<number> {
  const form = new FormData();
  form.append('file', file, file instanceof File ? file.name : 'photo.png');
  form.append('prompt', prompt);
  form.append('edit_car', String(editCar));
  form.append('size', size);
  const res = await apiClient.post<PreviewResponse>('/edit-photo/preview', form, {
    timeout: 180_000,
  });
  return res.data.photo_id;
}

export async function generatePhoto(photoId: number): Promise<Blob> {
  const res = await apiClient.post(`/edit-photo/${photoId}/generate`, undefined, {
    responseType: 'blob',
    timeout: 180_000,
  });
  return res.data as Blob;
}

export async function deletePreview(photoId: number): Promise<void> {
  await apiClient.delete(`/edit-photo/${photoId}/preview`);
}
