import { useCallback, useState } from 'react';
import { deletePreview, generatePhoto, previewPhoto } from '../api/segmentation';

export type EditPhotoStatus =
  | 'idle'
  | 'segmenting'
  | 'awaiting_confirmation'
  | 'generating'
  | 'success'
  | 'error';

export function useEditPhoto(onSuccess?: () => void) {
  const [status, setStatus] = useState<EditPhotoStatus>('idle');
  const [resultPhotoId, setResultPhotoId] = useState<number | null>(null);
  const [previewPhotoId, setPreviewPhotoId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (file: File | Blob, prompt: string, editCar: boolean) => {
    setStatus('segmenting');
    setError(null);
    setResultPhotoId(null);
    try {
      const photoId = await previewPhoto(file, prompt, editCar);
      setPreviewPhotoId(photoId);
      setStatus('awaiting_confirmation');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not segment the image.');
      setStatus('error');
    }
  }, []);

  const approve = useCallback(async () => {
    if (previewPhotoId === null) return;
    setStatus('generating');
    setError(null);
    try {
      await generatePhoto(previewPhotoId);
      setResultPhotoId(previewPhotoId);
      setPreviewPhotoId(null);
      setStatus('success');
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate the image.');
      setStatus('awaiting_confirmation');
    }
  }, [onSuccess, previewPhotoId]);

  const cancel = useCallback(async () => {
    if (previewPhotoId !== null) {
      await deletePreview(previewPhotoId);
    }
    setPreviewPhotoId(null);
    setResultPhotoId(null);
    setError(null);
    setStatus('idle');
  }, [previewPhotoId]);

  const reset = useCallback(() => {
    setPreviewPhotoId(null);
    setResultPhotoId(null);
    setError(null);
    setStatus('idle');
  }, []);

  return { status, resultPhotoId, previewPhotoId, error, submit, approve, cancel, reset };
}
