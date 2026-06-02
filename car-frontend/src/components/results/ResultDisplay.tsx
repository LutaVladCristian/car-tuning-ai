import { useEffect, useState } from 'react';
import {
  getEditMaskUrl,
  getOriginalPhotoUrl,
  getPhotoUrl,
  getRawMaskUrl,
} from '../../api/photos';
import type { EditPhotoStatus } from '../../hooks/useEditPhoto';
import ImageCompareSlider from './ImageCompareSlider';

interface Props {
  status: EditPhotoStatus;
  resultPhotoId: number | null;
  previewPhotoId: number | null;
  activePhotoId: number | null;
  error: string | null;
  onApprove: () => void;
  onCancel: () => void;
  onReset: () => void;
}

interface PhotoUrls {
  photoId: number;
  originalUrl: string | null;
  resultUrl: string | null;
  rawMaskUrl: string | null;
  editMaskUrl: string | null;
}

function Spinner() {
  return <div className="w-8 h-8 border-2 border-zinc-600 border-t-accent-blue rounded-full animate-spin" />;
}

const NO_CAR_DETECTED = 'No car is detected by the YOLO model.';

function MaskPreview({ urls }: { urls: PhotoUrls | null }) {
  if (!urls?.rawMaskUrl && !urls?.editMaskUrl) return null;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {urls.rawMaskUrl && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-zinc-400">SAM + YOLO Car Mask</p>
          <img src={urls.rawMaskUrl} alt="SAM and YOLO car mask" className="w-full rounded-lg border border-surface-600 bg-black object-contain aspect-[4/3]" />
        </div>
      )}
      {urls.editMaskUrl && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-zinc-400">OpenAI Editable Area</p>
          <div className="rounded-lg border border-surface-600 bg-[linear-gradient(45deg,#27272a_25%,transparent_25%),linear-gradient(-45deg,#27272a_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#27272a_75%),linear-gradient(-45deg,transparent_75%,#27272a_75%)] bg-[length:16px_16px] bg-[position:0_0,0_8px,8px_-8px,-8px_0px]">
            <img src={urls.editMaskUrl} alt="OpenAI editable area mask" className="w-full object-contain aspect-[4/3]" />
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResultDisplay({
  status,
  resultPhotoId,
  previewPhotoId,
  activePhotoId,
  error,
  onApprove,
  onCancel,
  onReset,
}: Props) {
  const displayPhotoId = previewPhotoId ?? activePhotoId;
  const [urls, setUrls] = useState<PhotoUrls | null>(null);
  const activeUrls = urls?.photoId === displayPhotoId ? urls : null;
  const isPreview = previewPhotoId !== null;

  useEffect(() => {
    if (displayPhotoId === null) return;
    const photoId = displayPhotoId;
    let active = true;
    const created: string[] = [];
    const optional = async (loader: (id: number) => Promise<string>) => {
      try {
        const url = await loader(photoId);
        created.push(url);
        return url;
      } catch {
        return null;
      }
    };
    async function load() {
      const [rawMaskUrl, editMaskUrl, originalUrl, resultUrl] = await Promise.all([
        optional(getRawMaskUrl),
        optional(getEditMaskUrl),
        isPreview ? Promise.resolve(null) : optional(getOriginalPhotoUrl),
        isPreview ? Promise.resolve(null) : optional(getPhotoUrl),
      ]);
      if (active) setUrls({ photoId, rawMaskUrl, editMaskUrl, originalUrl, resultUrl });
      else created.forEach(URL.revokeObjectURL);
    }
    void load();
    return () => {
      active = false;
      created.forEach(URL.revokeObjectURL);
    };
  }, [displayPhotoId, isPreview]);

  if (status === 'idle' && activePhotoId === null) {
    return <div className="flex items-center justify-center min-h-64 border-2 border-dashed border-surface-600 rounded-xl text-zinc-600 text-sm">Your result will appear here</div>;
  }
  if (status === 'segmenting') {
    return <div className="flex flex-col items-center justify-center min-h-64 gap-4"><Spinner /><p className="text-zinc-300 text-sm">Detecting car and preparing masks...</p></div>;
  }
  if (status === 'error') {
    const noCarDetected = error === NO_CAR_DETECTED;
    return <div role="alert" className="space-y-4 text-center py-8"><p className="text-red-400 text-sm">{noCarDetected ? 'No car detected' : 'Something went wrong'}</p><p className="text-zinc-500 text-xs">{error}</p><button type="button" onClick={onReset} className="text-xs border border-surface-600 px-4 py-1.5 rounded-md">Try again</button></div>;
  }
  if (isPreview) {
    return (
      <div className="space-y-4">
        <div>
          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Mask Preview</p>
          <p className="text-zinc-500 text-xs mt-1">Review the detected car and editable area before generating.</p>
        </div>
        {!activeUrls ? <div className="flex justify-center py-12"><Spinner /></div> : <MaskPreview urls={activeUrls} />}
        {error && <p className="text-red-400 text-xs">{error}</p>}
        {status === 'generating' ? (
          <div className="flex items-center justify-center gap-3 py-2"><Spinner /><span className="text-zinc-300 text-sm">OpenAI is generating your image...</span></div>
        ) : (
          <div className="flex gap-3">
            <button type="button" onClick={onApprove} className="flex-1 py-2.5 rounded-lg bg-accent-blue text-white text-sm font-medium">Generate Image</button>
            <button type="button" onClick={onCancel} className="px-4 py-2.5 rounded-lg border border-surface-600 text-zinc-400 text-sm">Cancel Preview</button>
          </div>
        )}
      </div>
    );
  }
  if (!activeUrls) return <div className="flex justify-center py-12"><Spinner /></div>;
  return (
    <div className="space-y-3">
      <div className="flex justify-between"><span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Compare</span><button type="button" onClick={onReset} className="text-xs text-zinc-500 border border-surface-600 px-3 py-1 rounded-md">New edit</button></div>
      {activeUrls.originalUrl && activeUrls.resultUrl ? (
        <>
          <ImageCompareSlider originalUrl={activeUrls.originalUrl} resultUrl={activeUrls.resultUrl} />
          <details className="border border-surface-600 rounded-lg p-3">
            <summary className="cursor-pointer text-xs text-zinc-400">View masks</summary>
            <div className="mt-3"><MaskPreview urls={activeUrls} /></div>
          </details>
          <a href={activeUrls.resultUrl} download="slick-tunes-result.png" className="w-full flex justify-center py-2.5 rounded-lg bg-accent-blue/10 border border-accent-blue/30 text-accent-blue text-sm font-medium">Save image to device</a>
        </>
      ) : <p className="text-red-400 text-xs">Could not load the comparison images.</p>}
      {activePhotoId === null && resultPhotoId === null && <p className="text-green-300 text-xs">Edit completed. Check your photo history.</p>}
    </div>
  );
}
