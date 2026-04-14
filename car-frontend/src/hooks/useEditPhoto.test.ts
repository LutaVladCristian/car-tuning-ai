import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useEditPhoto } from './useEditPhoto';

vi.mock('../api/segmentation', () => ({
  editPhoto: vi.fn(),
}));

vi.mock('../api/photos', () => ({
  listPhotos: vi.fn(),
}));

import { editPhoto } from '../api/segmentation';
import { listPhotos } from '../api/photos';

const mockEditPhoto = vi.mocked(editPhoto);
const mockListPhotos = vi.mocked(listPhotos);

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useEditPhoto', () => {
  it('starts in idle state', () => {
    const { result } = renderHook(() => useEditPhoto());

    expect(result.current.status).toBe('idle');
    expect(result.current.resultPhotoId).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('transitions to success and sets resultPhotoId when a new photo appears', async () => {
    mockListPhotos
      .mockResolvedValueOnce({ photos: [], total: 0 })              // before snapshot
      .mockResolvedValueOnce({ photos: [{ id: 42 } as never], total: 1 }); // first poll
    mockEditPhoto.mockResolvedValueOnce(new Blob());

    const { result } = renderHook(() => useEditPhoto());

    await act(async () => {
      const submitPromise = result.current.submit(new Blob(), 'make it red', true);
      // Advance past the sleep(500) and flush all resulting microtasks
      await vi.advanceTimersByTimeAsync(600);
      await submitPromise;
    });

    expect(result.current.status).toBe('success');
    expect(result.current.resultPhotoId).toBe(42);
  });

  it('transitions to error and captures the message on API failure', async () => {
    mockListPhotos.mockResolvedValueOnce({ photos: [], total: 0 });
    mockEditPhoto.mockRejectedValueOnce(new Error('Request timed out'));

    const { result } = renderHook(() => useEditPhoto());

    await act(async () => {
      await result.current.submit(new Blob(), 'make it red', true);
    });

    expect(result.current.status).toBe('error');
    expect(result.current.error).toBe('Request timed out');
    expect(result.current.resultPhotoId).toBeNull();
  });

  it('sets resultPhotoId to null when polling exhausts without a new photo', async () => {
    // Always returns the same total — no new photo ever appears
    mockListPhotos.mockResolvedValue({ photos: [], total: 0 });
    mockEditPhoto.mockResolvedValueOnce(new Blob());

    const { result } = renderHook(() => useEditPhoto());

    await act(async () => {
      const submitPromise = result.current.submit(new Blob(), 'prompt', true);
      // Advance through all 10 polling intervals (10 × 500 ms = 5 s)
      await vi.advanceTimersByTimeAsync(5100);
      await submitPromise;
    });

    expect(result.current.status).toBe('success');
    expect(result.current.resultPhotoId).toBeNull();
  });

  it('calls the onSuccess callback exactly once after a successful submission', async () => {
    mockListPhotos
      .mockResolvedValueOnce({ photos: [], total: 0 })
      .mockResolvedValueOnce({ photos: [{ id: 7 } as never], total: 1 });
    mockEditPhoto.mockResolvedValueOnce(new Blob());

    const onSuccess = vi.fn();
    const { result } = renderHook(() => useEditPhoto(onSuccess));

    await act(async () => {
      const submitPromise = result.current.submit(new Blob(), 'prompt', false);
      await vi.advanceTimersByTimeAsync(600);
      await submitPromise;
    });

    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('resets back to idle state after a successful submission', async () => {
    mockListPhotos
      .mockResolvedValueOnce({ photos: [], total: 0 })
      .mockResolvedValueOnce({ photos: [{ id: 1 } as never], total: 1 });
    mockEditPhoto.mockResolvedValueOnce(new Blob());

    const { result } = renderHook(() => useEditPhoto());

    await act(async () => {
      const submitPromise = result.current.submit(new Blob(), 'prompt', true);
      await vi.advanceTimersByTimeAsync(600);
      await submitPromise;
    });

    expect(result.current.status).toBe('success');

    act(() => {
      result.current.reset();
    });

    expect(result.current.status).toBe('idle');
    expect(result.current.resultPhotoId).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
