import { useState, useEffect, useCallback } from 'react';
import { listPhotos } from '../api/photos';
import type { PhotoResponse } from '../types/photo';

interface UsePhotoHistoryReturn {
  photos: PhotoResponse[];
  total: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
  fetchMore: () => void;
  hasMore: boolean;
}

const PAGE_SIZE = 20;

export function usePhotoHistory(): UsePhotoHistoryReturn {
  const [photos, setPhotos] = useState<PhotoResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (offset: number, replace: boolean) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listPhotos(offset, PAGE_SIZE);
      setPhotos((prev) => (replace ? data.photos : [...prev, ...data.photos]));
      setTotal(data.total);
    } catch (err) {
      // H12: Log original error so it isn't silently swallowed.
      console.error('Failed to load photo history:', err);
      setError('Failed to load photo history.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load(0, true);
  }, [load]);

  const refetch = useCallback(() => {
    setSkip(0);
    load(0, true);
  }, [load]);

  const fetchMore = useCallback(() => {
    const nextSkip = skip + PAGE_SIZE;
    setSkip(nextSkip);
    load(nextSkip, false);
  }, [skip, load]);

  return {
    photos,
    total,
    isLoading,
    error,
    refetch,
    fetchMore,
    hasMore: photos.length < total,
  };
}
