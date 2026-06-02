import { apiClient } from './client';

export interface PreviewResponse {
  photo_id: number;
}

async function getBlobErrorDetail(err: unknown): Promise<string | null> {
  const data = (err as { response?: { data?: unknown } }).response?.data;
  if (!(data instanceof Blob)) {
    return null;
  }

  try {
    const payload = JSON.parse(await data.text()) as { detail?: unknown };
    return typeof payload.detail === 'string' ? payload.detail : null;
  } catch {
    return null;
  }
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
  try {
    const res = await apiClient.post(`/edit-photo/${photoId}/generate`, undefined, {
      responseType: 'blob',
      timeout: 180_000,
    });
    return res.data as Blob;
  } catch (err) {
    const detail = await getBlobErrorDetail(err);
    throw detail ? new Error(detail) : err;
  }
}

export async function deletePreview(photoId: number): Promise<void> {
  await apiClient.delete(`/edit-photo/${photoId}/preview`);
}
