import { useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import type { ImageSourceType } from '../../types/tuning';
import type { PhotoResponse } from '../../types/photo';

interface Props {
  imageSource: ImageSourceType;
  uploadedFile: File | null;
  selectedHistoryPhotoId: number | null;
  historyPhotos: PhotoResponse[];
  onSourceChange: (source: ImageSourceType) => void;
  onFileUpload: (file: File) => void;
  onHistorySelect: (photoId: number) => void;
}

export default function ImageSelector({
  imageSource,
  uploadedFile,
  selectedHistoryPhotoId,
  historyPhotos,
  onSourceChange,
  onFileUpload,
  onHistorySelect,
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const previewUrl = uploadedFile ? URL.createObjectURL(uploadedFile) : null;

  const handleFile = (file: File) => {
    if (file.type.startsWith('image/')) onFileUpload(file);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onSourceChange('upload')}
          className={`flex-1 py-1.5 px-3 rounded-md text-xs font-medium transition-colors ${
            imageSource === 'upload'
              ? 'bg-surface-600 text-zinc-100'
              : 'bg-surface-700 text-zinc-500 hover:text-zinc-300'
          }`}
        >
          Upload new
        </button>
        <button
          type="button"
          onClick={() => onSourceChange('history')}
          className={`flex-1 py-1.5 px-3 rounded-md text-xs font-medium transition-colors ${
            imageSource === 'history'
              ? 'bg-surface-600 text-zinc-100'
              : 'bg-surface-700 text-zinc-500 hover:text-zinc-300'
          }`}
        >
          From history ({historyPhotos.length})
        </button>
      </div>

      {imageSource === 'upload' && (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onClick={() => fileInputRef.current?.click()}
          className={`relative cursor-pointer rounded-xl border-2 border-dashed transition-colors ${
            isDragging
              ? 'border-accent-blue bg-accent-blue/5'
              : 'border-surface-600 hover:border-zinc-500 bg-surface-700'
          } flex flex-col items-center justify-center min-h-[160px]`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleChange}
          />
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Selected car"
              className="max-h-48 rounded-lg object-contain"
            />
          ) : (
            <div className="text-center px-4 py-6">
              <div className="text-3xl mb-2">📷</div>
              <p className="text-zinc-400 text-sm">Drop image here or click to browse</p>
              <p className="text-zinc-600 text-xs mt-1">JPG, PNG, WEBP</p>
            </div>
          )}
          {uploadedFile && (
            <p className="absolute bottom-2 right-3 text-xs text-zinc-500">
              {uploadedFile.name}
            </p>
          )}
        </div>
      )}

      {imageSource === 'history' && (
        <div className="bg-surface-700 border border-surface-600 rounded-xl overflow-hidden">
          {historyPhotos.length === 0 ? (
            <p className="text-center text-zinc-500 text-sm py-8">No photos in history yet.</p>
          ) : (
            <select
              value={selectedHistoryPhotoId ?? ''}
              onChange={(e) => onHistorySelect(Number(e.target.value))}
              className="w-full bg-surface-700 text-zinc-100 text-sm px-4 py-3 focus:outline-none focus:ring-1 focus:ring-accent-blue"
              size={Math.min(historyPhotos.length, 6)}
            >
              <option value="" disabled className="text-zinc-500">
                — Select a photo —
              </option>
              {historyPhotos.map((p) => (
                <option key={p.id} value={p.id} className="bg-surface-700 py-1">
                  #{p.id} · {p.original_filename} · {p.operation_type.replace('_', ' ')} · {formatDate(p.created_at)}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  );
}
