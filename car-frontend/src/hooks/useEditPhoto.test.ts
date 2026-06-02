import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useEditPhoto } from './useEditPhoto';

vi.mock('../api/segmentation', () => ({
  previewPhoto: vi.fn(),
  generatePhoto: vi.fn(),
  deletePreview: vi.fn(),
}));

import { deletePreview, generatePhoto, previewPhoto } from '../api/segmentation';

const mockPreview = vi.mocked(previewPhoto);
const mockGenerate = vi.mocked(generatePhoto);
const mockDelete = vi.mocked(deletePreview);

beforeEach(() => vi.clearAllMocks());

describe('useEditPhoto', () => {
  it('creates a mask preview before generation', async () => {
    mockPreview.mockResolvedValueOnce(42);
    const { result } = renderHook(() => useEditPhoto());
    await act(async () => result.current.submit(new Blob(), 'red', true));
    expect(result.current.status).toBe('awaiting_confirmation');
    expect(result.current.previewPhotoId).toBe(42);
    expect(mockGenerate).not.toHaveBeenCalled();
  });

  it('shows the YOLO no-car message returned by the API', async () => {
    mockPreview.mockRejectedValueOnce({
      response: { data: { detail: 'No car is detected by the YOLO model.' } },
    });
    const { result } = renderHook(() => useEditPhoto());
    await act(async () => result.current.submit(new Blob(), 'red', true));
    expect(result.current.status).toBe('error');
    expect(result.current.error).toBe('No car is detected by the YOLO model.');
  });

  it('generates an approved preview and reports success', async () => {
    mockPreview.mockResolvedValueOnce(42);
    mockGenerate.mockResolvedValueOnce(new Blob());
    const onSuccess = vi.fn();
    const { result } = renderHook(() => useEditPhoto(onSuccess));
    await act(async () => result.current.submit(new Blob(), 'red', true));
    await act(async () => result.current.approve());
    expect(mockGenerate).toHaveBeenCalledWith(42);
    expect(result.current.status).toBe('success');
    expect(result.current.resultPhotoId).toBe(42);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('deletes a canceled preview', async () => {
    mockPreview.mockResolvedValueOnce(7);
    mockDelete.mockResolvedValueOnce();
    const { result } = renderHook(() => useEditPhoto());
    await act(async () => result.current.submit(new Blob(), 'red', true));
    await act(async () => result.current.cancel());
    expect(mockDelete).toHaveBeenCalledWith(7);
    expect(result.current.status).toBe('idle');
  });

  it('keeps a preview approvable after generation fails', async () => {
    mockPreview.mockResolvedValueOnce(7);
    mockGenerate.mockRejectedValueOnce(new Error('provider down'));
    const { result } = renderHook(() => useEditPhoto());
    await act(async () => result.current.submit(new Blob(), 'red', true));
    await act(async () => result.current.approve());
    expect(result.current.status).toBe('awaiting_confirmation');
    expect(result.current.previewPhotoId).toBe(7);
    expect(result.current.error).toBe('provider down');
  });
});
