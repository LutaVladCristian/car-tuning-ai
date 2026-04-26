import type { PhotoResponse } from '../../types/photo';

const OP_LABELS: Record<string, string> = {
  car_segmentation: 'Car Seg',
  car_part_segmentation: 'Part Seg',
  edit_photo: 'AI Edit',
};

const OP_COLORS: Record<string, string> = {
  car_segmentation: 'bg-blue-500/20 text-blue-400',
  car_part_segmentation: 'bg-purple-500/20 text-purple-400',
  edit_photo: 'bg-orange-500/20 text-orange-400',
};

interface Props {
  photos: PhotoResponse[];
  total: number;
  isLoading: boolean;
  hasMore: boolean;
  selectedPhotoId?: number | null;
  onLoadMore: () => void;
  onSelectPhoto: (id: number) => void;
}

export default function PhotoHistoryPanel({
  photos,
  total,
  isLoading,
  hasMore,
  selectedPhotoId = null,
  onLoadMore,
  onSelectPhoto,
}: Props) {
  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          History
        </span>
        <span className="text-xs text-zinc-600">{total} total</span>
      </div>

      {photos.length === 0 && !isLoading && (
        <p className="text-center text-zinc-600 text-sm py-6">No photos yet.</p>
      )}

      <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
        {photos.map((photo) => {
          const isSelected = photo.id === selectedPhotoId;
          return (
            <button
              key={photo.id}
              type="button"
              onClick={() => onSelectPhoto(photo.id)}
              className={`w-full text-left bg-surface-700 hover:bg-surface-600 border rounded-lg px-3 py-2.5 transition-colors ${
                isSelected
                  ? 'border-accent-blue/70 ring-1 ring-accent-blue/40'
                  : 'border-surface-600 hover:border-zinc-500'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-zinc-300 text-xs truncate flex-1">
                  {photo.original_filename}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${OP_COLORS[photo.operation_type] ?? 'bg-zinc-700 text-zinc-400'}`}>
                  {OP_LABELS[photo.operation_type] ?? photo.operation_type}
                </span>
              </div>
              <p className="text-zinc-600 text-xs mt-0.5">{formatDate(photo.created_at)}</p>
            </button>
          );
        })}
      </div>

      {isLoading && (
        <p className="text-center text-zinc-600 text-xs py-2">Loading...</p>
      )}

      {hasMore && !isLoading && (
        <button
          type="button"
          onClick={onLoadMore}
          className="w-full text-xs text-zinc-500 hover:text-zinc-300 py-2 border border-surface-600 rounded-lg transition-colors"
        >
          Load more
        </button>
      )}
    </div>
  );
}
