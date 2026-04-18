import { apiClient } from './client';

export async function editPhoto(
  file: File | Blob,
  prompt: string,
  editCar: boolean,
  size = 'auto'
): Promise<Blob> {
  const form = new FormData();
  form.append('file', file, file instanceof File ? file.name : 'photo.png');
  form.append('prompt', prompt);
  form.append('edit_car', String(editCar));
  form.append('size', size);

  const res = await apiClient.post('/edit-photo', form, {
    responseType: 'blob',
    timeout: 180_000,
  });
  return res.data as Blob;
}


