import { useEffect, useState } from 'react';
import { getPhotoUrl } from '../../api/photos';
import type { EditPhotoStatus } from '../../hooks/useEditPhoto';

interface Props {
  status: EditPhotoStatus;
  resultPhotoId: number | null;
  error: string | null;
  onReset: () => void;
}

function Spinner() {
  return (
    <div className="w-8 h-8 border-2 border-zinc-600 border-t-accent-blue rounded-full animate-spin" />
  );
}

export default function ResultDisplay({ status, resultPhotoId, error, onReset }: Props) {
  const [imgResult, setImgResult] = useState<{ photoId: number; url: string | null } | null>(null);
  const imgUrl = imgResult?.photoId === resultPhotoId ? imgResult.url : null;
  const imgLoading =
    status === 'success' && resultPhotoId !== null && imgResult?.photoId !== resultPhotoId;

  useEffect(() => {
    if (status !== 'success' || resultPhotoId === null) return;

    let isActive = true;
    let blobUrl: string | null = null;

    getPhotoUrl(resultPhotoId)
      .then((url) => {
        if (isActive) {
          blobUrl = url;
          setImgResult({ photoId: resultPhotoId, url });
        } else {
          // H11: Discard immediately if the effect was already cleaned up.
          URL.revokeObjectURL(url);
        }
      })
      .catch(() => {
        if (isActive) setImgResult({ photoId: resultPhotoId, url: null });
      });

    return () => {
      isActive = false;
      // H11: Revoke the blob URL when resultPhotoId changes or component unmounts.
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [status, resultPhotoId]);

  if (status === 'idle') {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 border-2 border-dashed border-surface-600 rounded-xl text-zinc-600">
        <div className="text-4xl mb-3">🚗</div>
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
        <div className="text-3xl">⚠️</div>
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

  // success
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Result</span>
        <div className="flex items-center gap-2">
          {imgUrl && (
            <a
              href={imgUrl}
              download="tuned-car.png"
              className="text-xs text-zinc-500 hover:text-zinc-300 border border-surface-600 px-3 py-1 rounded-md transition-colors"
            >
              Download
            </a>
          )}
          <button
            type="button"
            onClick={onReset}
            className="text-xs text-zinc-500 hover:text-zinc-300 border border-surface-600 px-3 py-1 rounded-md transition-colors"
          >
            New edit
          </button>
        </div>
      </div>

      {imgLoading && (
        <div className="flex items-center justify-center min-h-48 bg-surface-800 border border-surface-600 rounded-xl">
          <Spinner />
        </div>
      )}

      {!imgLoading && imgUrl && (
        <div className="rounded-xl overflow-hidden border border-surface-600">
          <img src={imgUrl} alt="Edited car" className="w-full object-contain" />
        </div>
      )}

      {!imgLoading && !imgUrl && !resultPhotoId && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg px-4 py-3 text-xs text-green-300">
          Edit submitted successfully. Check your photo history for the saved record.
        </div>
      )}
    </div>
  );
}
