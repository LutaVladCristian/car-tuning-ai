import { useState, useCallback } from 'react';
import { editPhoto } from '../api/segmentation';
import { listPhotos } from '../api/photos';

export type EditPhotoStatus = 'idle' | 'submitting' | 'polling' | 'success' | 'error';

interface UseEditPhotoReturn {
  status: EditPhotoStatus;
  resultPhotoId: number | null;
  error: string | null;
  submit: (file: File | Blob, prompt: string, editCar: boolean) => Promise<void>;
  reset: () => void;
}

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

export function useEditPhoto(onSuccess?: () => void): UseEditPhotoReturn {
  const [status, setStatus] = useState<EditPhotoStatus>('idle');
  const [resultPhotoId, setResultPhotoId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (file: File | Blob, prompt: string, editCar: boolean) => {
      setStatus('submitting');
      setError(null);
      setResultPhotoId(null);

      try {
        // Snapshot current count before submitting
        const before = await listPhotos(0, 1);
        const beforeTotal = before.total;

        // This call blocks for 30-90s while OpenAI processes
        await editPhoto(file, prompt, editCar);

        // Poll for the new DB record (insert is synchronous before response)
        setStatus('polling');
        let newId: number | null = null;
        for (let i = 0; i < 10; i++) {
          await sleep(500);
          const after = await listPhotos(0, 1);
          if (after.total > beforeTotal) {
            newId = after.photos[0]?.id ?? null;
            break;
          }
        }

        setResultPhotoId(newId);
        setStatus('success');
        onSuccess?.();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'An error occurred. Please try again.';
        setError(message);
        setStatus('error');
      }
    },
    [onSuccess]
  );

  const reset = useCallback(() => {
    setStatus('idle');
    setResultPhotoId(null);
    setError(null);
  }, []);

  return { status, resultPhotoId, error, submit, reset };
}
