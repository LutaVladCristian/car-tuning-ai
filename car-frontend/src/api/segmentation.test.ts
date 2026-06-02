import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiClient: {
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from './client';
import { generatePhoto } from './segmentation';

const mockPost = vi.mocked(apiClient.post);

beforeEach(() => vi.clearAllMocks());

describe('generatePhoto', () => {
  it('returns the generated image blob', async () => {
    const blob = new Blob(['image']);
    mockPost.mockResolvedValueOnce({ data: blob });

    await expect(generatePhoto(7)).resolves.toBe(blob);
  });

  it('surfaces FastAPI details from blob error responses', async () => {
    const detail = 'OpenAI rejected the prepared image or mask. Please try another image.';
    mockPost.mockRejectedValueOnce({
      response: {
        data: new Blob([JSON.stringify({ detail })], { type: 'application/json' }),
      },
    });

    await expect(generatePhoto(7)).rejects.toThrow(detail);
  });
});
