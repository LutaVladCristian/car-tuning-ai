import { useEffect, useState } from 'react';
import { getOriginalPhotoUrl, getPhotoUrl } from '../../api/photos';
import type { EditPhotoStatus } from '../../hooks/useEditPhoto';
import ImageCompareSlider from './ImageCompareSlider';

interface Props {
  status: EditPhotoStatus;
  resultPhotoId: number | null;
  activePhotoId: number | null;
  error: string | null;
  onReset: () => void;
}

function Spinner() {
  return (
    <div className="w-8 h-8 border-2 border-zinc-600 border-t-accent-blue rounded-full animate-spin" />
  );
}

export default function ResultDisplay({
  status,
  resultPhotoId,
  activePhotoId,
  error,
  onReset,
}: Props) {
  const [imgResult, setImgResult] = useState<{
    photoId: number;
    originalUrl: string | null;
    resultUrl: string | null;
  } | null>(null);
  const activeUrls = imgResult?.photoId === activePhotoId ? imgResult : null;
  const imgLoading = activePhotoId !== null && imgResult?.photoId !== activePhotoId;

  useEffect(() => {
    if (activePhotoId === null) return;

    const photoId = activePhotoId;
    let isActive = true;
    let originalBlobUrl: string | null = null;
    let resultBlobUrl: string | null = null;

    async function loadImages() {
      try {
        const originalUrl = await getOriginalPhotoUrl(photoId);
        originalBlobUrl = originalUrl;
        const resultUrl = await getPhotoUrl(photoId);
        resultBlobUrl = resultUrl;

        if (isActive) {
          setImgResult({ photoId, originalUrl, resultUrl });
        } else {
          URL.revokeObjectURL(originalUrl);
          URL.revokeObjectURL(resultUrl);
        }
      } catch {
        if (originalBlobUrl) {
          URL.revokeObjectURL(originalBlobUrl);
          originalBlobUrl = null;
        }
        if (resultBlobUrl) {
          URL.revokeObjectURL(resultBlobUrl);
          resultBlobUrl = null;
        }
        if (isActive) {
          setImgResult({ photoId, originalUrl: null, resultUrl: null });
        }
      }
    }

    void loadImages();

    return () => {
      isActive = false;
      if (originalBlobUrl) URL.revokeObjectURL(originalBlobUrl);
      if (resultBlobUrl) URL.revokeObjectURL(resultBlobUrl);
    };
  }, [activePhotoId]);

  if (status === 'idle' && activePhotoId === null) {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 border-2 border-dashed border-surface-600 rounded-xl text-zinc-600">
        <div className="text-4xl mb-3">CAR</div>
        <p className="text-sm">Your result will appear here</p>
      </div>
    );
  }

  if (status === 'submitting') {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 bg-surface-800 border border-surface-600 rounded-xl gap-4">
        <Spinner />
        <div className="text-center">
          <p className="text-zinc-300 text-sm font-medium">Sending to AI...</p>
          <p className="text-zinc-500 text-xs mt-1">OpenAI is processing your image</p>
        </div>
      </div>
    );
  }

  if (status === 'polling') {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 bg-surface-800 border border-surface-600 rounded-xl gap-4">
        <Spinner />
        <div className="text-center">
          <p className="text-zinc-300 text-sm font-medium">Saving result...</p>
          <p className="text-zinc-500 text-xs mt-1">Finalizing your photo record</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 bg-red-500/5 border border-red-500/20 rounded-xl gap-4 px-6 text-center">
        <div className="text-3xl">!</div>
        <div>
          <p className="text-red-400 text-sm font-medium">Something went wrong</p>
          <p className="text-zinc-500 text-xs mt-1">{error}</p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="text-xs text-zinc-400 hover:text-zinc-200 border border-surface-600 px-4 py-1.5 rounded-md transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          Compare
        </span>
        <button
          type="button"
          onClick={onReset}
          className="text-xs text-zinc-500 hover:text-zinc-300 border border-surface-600 px-3 py-1 rounded-md transition-colors"
        >
          New edit
        </button>
      </div>

      {imgLoading && (
        <div className="flex items-center justify-center min-h-48 bg-surface-800 border border-surface-600 rounded-xl">
          <Spinner />
        </div>
      )}

      {!imgLoading && activeUrls?.originalUrl && activeUrls.resultUrl && (
        <div className="space-y-3">
          <ImageCompareSlider
            originalUrl={activeUrls.originalUrl}
            resultUrl={activeUrls.resultUrl}
          />
          <a
            href={activeUrls.resultUrl}
            download="slick-tunes-result.png"
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-accent-blue/10 border border-accent-blue/30 text-accent-blue text-sm font-medium hover:bg-accent-blue/20 transition-colors"
          >
            Save image to device
          </a>
        </div>
      )}

      {!imgLoading && activePhotoId === null && resultPhotoId === null && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg px-4 py-3 text-xs text-green-300">
          Edit submitted successfully. Check your photo history for the saved record.
        </div>
      )}

      {!imgLoading && activePhotoId !== null && (!activeUrls?.originalUrl || !activeUrls.resultUrl) && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg px-4 py-3 text-xs text-red-400">
          Could not load the comparison images. Try selecting another photo.
        </div>
      )}
    </div>
  );
}
