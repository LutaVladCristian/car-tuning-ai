import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ResultDisplay from './ResultDisplay';

vi.mock('../../api/photos', () => ({
  getPhotoUrl: vi.fn(),
  getOriginalPhotoUrl: vi.fn(),
  getRawMaskUrl: vi.fn(),
  getEditMaskUrl: vi.fn(),
}));

import { getEditMaskUrl, getOriginalPhotoUrl, getPhotoUrl, getRawMaskUrl } from '../../api/photos';
const mockOriginal = vi.mocked(getOriginalPhotoUrl);
const mockResult = vi.mocked(getPhotoUrl);
const mockRawMask = vi.mocked(getRawMaskUrl);
const mockEditMask = vi.mocked(getEditMaskUrl);

const base = {
  status: 'idle' as const,
  resultPhotoId: null,
  previewPhotoId: null,
  activePhotoId: null,
  error: null,
  onApprove: vi.fn(),
  onCancel: vi.fn(),
  onReset: vi.fn(),
};

beforeEach(() => vi.clearAllMocks());

describe('ResultDisplay', () => {
  it('renders the idle placeholder', () => {
    render(<ResultDisplay {...base} />);
    expect(screen.getByText('Your result will appear here')).toBeDefined();
  });

  it('shows a dedicated notification when YOLO detects no car', () => {
    render(<ResultDisplay {...base} status="error" error="No car is detected by the YOLO model." />);
    expect(screen.getByRole('alert')).toBeDefined();
    expect(screen.getByText('No car detected')).toBeDefined();
    expect(screen.getByText('No car is detected by the YOLO model.')).toBeDefined();
  });

  it('shows both masks before approval', async () => {
    mockRawMask.mockResolvedValueOnce('blob:raw');
    mockEditMask.mockResolvedValueOnce('blob:edit');
    render(<ResultDisplay {...base} status="awaiting_confirmation" previewPhotoId={4} />);
    expect(await waitFor(() => screen.getByAltText('SAM and YOLO car mask'))).toBeDefined();
    expect(screen.getByAltText('OpenAI editable area mask')).toBeDefined();
    expect(screen.getByText('Generate Image')).toBeDefined();
  });

  it('calls approval and cancellation actions', async () => {
    mockRawMask.mockResolvedValue('blob:raw');
    mockEditMask.mockResolvedValue('blob:edit');
    const onApprove = vi.fn();
    const onCancel = vi.fn();
    render(<ResultDisplay {...base} status="awaiting_confirmation" previewPhotoId={4} onApprove={onApprove} onCancel={onCancel} />);
    await waitFor(() => screen.getByText('Generate Image'));
    fireEvent.click(screen.getByText('Generate Image'));
    fireEvent.click(screen.getByText('Cancel Preview'));
    expect(onApprove).toHaveBeenCalledTimes(1);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('renders completed comparison and collapsed masks', async () => {
    mockOriginal.mockResolvedValueOnce('blob:original');
    mockResult.mockResolvedValueOnce('blob:result');
    mockRawMask.mockResolvedValueOnce('blob:raw');
    mockEditMask.mockResolvedValueOnce('blob:edit');
    render(<ResultDisplay {...base} status="success" resultPhotoId={4} activePhotoId={4} />);
    expect(await waitFor(() => screen.getByAltText('Generated car'))).toBeDefined();
    expect(screen.getByText('View masks')).toBeDefined();
    expect(screen.getByText('Save image to device')).toBeDefined();
  });
});
