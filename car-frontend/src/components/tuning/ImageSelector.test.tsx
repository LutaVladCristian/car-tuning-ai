import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import ImageSelector from './ImageSelector';

const defaultProps = {
  imageSource: 'upload' as const,
  uploadedFile: null,
  selectedHistoryPhotoId: null,
  historyPhotos: [],
  onSourceChange: vi.fn(),
  onFileUpload: vi.fn(),
  onHistorySelect: vi.fn(),
};

describe('ImageSelector', () => {
  it('restricts the file input to png, jpeg, and webp', () => {
    const { container } = render(<ImageSelector {...defaultProps} />);

    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();
    expect(input?.getAttribute('accept')).toBe('image/png,image/jpeg,image/webp');
  });

  it('rejects unsupported file formats before upload', () => {
    const onFileUpload = vi.fn();
    const { container } = render(<ImageSelector {...defaultProps} onFileUpload={onFileUpload} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File([new Uint8Array([1, 2, 3])], 'car.gif', { type: 'image/gif' });
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileUpload).not.toHaveBeenCalled();
    expect(screen.getByText('Unsupported image format. Upload a JPEG, PNG, or WEBP file.')).toBeTruthy();
  });

  it('rejects files larger than 10 MB before upload', () => {
    const onFileUpload = vi.fn();
    const { container } = render(<ImageSelector {...defaultProps} onFileUpload={onFileUpload} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File([new Uint8Array((10 * 1024 * 1024) + 1)], 'car.png', { type: 'image/png' });
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileUpload).not.toHaveBeenCalled();
    expect(screen.getByText('File is too large. Maximum size is 10 MB.')).toBeTruthy();
  });
});
