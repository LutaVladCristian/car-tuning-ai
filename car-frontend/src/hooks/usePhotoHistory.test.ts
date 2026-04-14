import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { usePhotoHistory } from './usePhotoHistory';

vi.mock('../api/photos', () => ({
  listPhotos: vi.fn(),
}));

import { listPhotos } from '../api/photos';

const mockListPhotos = vi.mocked(listPhotos);

const makePage = (ids: number[], total: number) => ({
  photos: ids.map((id) => ({ id }) as never),
  total,
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe('usePhotoHistory', () => {
  it('fetches the first page on mount with correct pagination params', async () => {
    mockListPhotos.mockResolvedValueOnce(makePage([1, 2, 3], 3));

    const { result } = renderHook(() => usePhotoHistory());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockListPhotos).toHaveBeenCalledWith(0, 20);
    expect(result.current.photos).toHaveLength(3);
    expect(result.current.total).toBe(3);
  });

  it('reports hasMore as true when there are more photos to load', async () => {
    mockListPhotos.mockResolvedValueOnce(makePage([1, 2], 10));

    const { result } = renderHook(() => usePhotoHistory());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.hasMore).toBe(true);
  });

  it('reports hasMore as false when all photos are loaded', async () => {
    mockListPhotos.mockResolvedValueOnce(makePage([1, 2], 2));

    const { result } = renderHook(() => usePhotoHistory());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.hasMore).toBe(false);
  });

  it('appends the next page on fetchMore without replacing existing photos', async () => {
    mockListPhotos
      .mockResolvedValueOnce(makePage([1, 2], 4))   // initial load
      .mockResolvedValueOnce(makePage([3, 4], 4));   // fetchMore

    const { result } = renderHook(() => usePhotoHistory());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.fetchMore();
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockListPhotos).toHaveBeenCalledWith(20, 20);
    expect(result.current.photos).toHaveLength(4);
  });

  it('replaces photos and resets to page 0 on refetch', async () => {
    mockListPhotos
      .mockResolvedValueOnce(makePage([1, 2], 4))   // initial load
      .mockResolvedValueOnce(makePage([3, 4], 4))   // fetchMore
      .mockResolvedValueOnce(makePage([1, 2], 4));   // refetch

    const { result } = renderHook(() => usePhotoHistory());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => { result.current.fetchMore(); });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => { result.current.refetch(); });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // The last listPhotos call should be back to skip=0
    expect(mockListPhotos).toHaveBeenLastCalledWith(0, 20);
    // Should only have 2 photos (the replaced page), not 4 accumulated
    expect(result.current.photos).toHaveLength(2);
  });

  it('sets error message when the API call fails', async () => {
    mockListPhotos.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => usePhotoHistory());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.error).toBe('Failed to load photo history.');
    expect(result.current.photos).toHaveLength(0);
  });
});
