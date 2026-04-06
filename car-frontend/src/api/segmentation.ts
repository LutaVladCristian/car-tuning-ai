import { apiClient } from './client';

export async function editPhoto(
  file: File | Blob,
  prompt: string,
  editCar: boolean,
  size = '1024x1536'
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

export async function carSegmentation(file: File, inverse: boolean): Promise<Blob> {
  const form = new FormData();
  form.append('file', file);
  form.append('inverse', String(inverse));

  const res = await apiClient.post('/car-segmentation', form, {
    responseType: 'blob',
    timeout: 120_000,
  });
  return res.data as Blob;
}

export async function carPartSegmentation(
  file: File,
  carPartId: number,
  inverse: boolean
): Promise<Blob> {
  const form = new FormData();
  form.append('file', file);
  form.append('carPartId', String(carPartId));
  form.append('inverse', String(inverse));

  const res = await apiClient.post('/car-part-segmentation', form, {
    responseType: 'blob',
    timeout: 120_000,
  });
  return res.data as Blob;
}
