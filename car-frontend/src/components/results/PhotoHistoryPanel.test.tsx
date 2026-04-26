import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PhotoHistoryPanel from './PhotoHistoryPanel';
import type { PhotoResponse } from '../../types/photo';

function makePhoto(overrides: Partial<PhotoResponse> = {}): PhotoResponse {
  return {
    id: 1,
    user_id: 1,
    original_filename: 'car.jpg',
    operation_type: 'edit_photo',
    operation_params: null,
    created_at: '2026-04-14T12:00:00Z',
    ...overrides,
  };
}

const defaultProps = {
  photos: [],
  total: 0,
  isLoading: false,
  hasMore: false,
  onLoadMore: vi.fn(),
  onSelectPhoto: vi.fn(),
};

describe('PhotoHistoryPanel', () => {
  it('shows "No photos yet." when the list is empty and not loading', () => {
    render(<PhotoHistoryPanel {...defaultProps} />);
    expect(screen.getByText('No photos yet.')).toBeDefined();
  });

  it('renders photo filenames in the list', () => {
    const photos = [
      makePhoto({ id: 1, original_filename: 'sports-car.png' }),
      makePhoto({ id: 2, original_filename: 'sedan.jpg' }),
    ];
    render(<PhotoHistoryPanel {...defaultProps} photos={photos} total={2} />);
    expect(screen.getByText('sports-car.png')).toBeDefined();
    expect(screen.getByText('sedan.jpg')).toBeDefined();
  });

  it('maps operation_type to the correct label', () => {
    const photos = [
      makePhoto({ id: 1, operation_type: 'car_segmentation' }),
      makePhoto({ id: 2, operation_type: 'car_part_segmentation' }),
      makePhoto({ id: 3, operation_type: 'edit_photo' }),
    ];
    render(<PhotoHistoryPanel {...defaultProps} photos={photos} total={3} />);
    expect(screen.getByText('Car Seg')).toBeDefined();
    expect(screen.getByText('Part Seg')).toBeDefined();
    expect(screen.getByText('AI Edit')).toBeDefined();
  });

  it('shows the total photo count', () => {
    render(<PhotoHistoryPanel {...defaultProps} total={42} />);
    expect(screen.getByText('42 total')).toBeDefined();
  });

  it('shows the Load more button when hasMore is true', () => {
    const photos = [makePhoto()];
    render(<PhotoHistoryPanel {...defaultProps} photos={photos} total={5} hasMore={true} />);
    expect(screen.getByText('Load more')).toBeDefined();
  });

  it('hides the Load more button when hasMore is false', () => {
    render(<PhotoHistoryPanel {...defaultProps} />);
    expect(screen.queryByText('Load more')).toBeNull();
  });

  it('calls onLoadMore when the Load more button is clicked', () => {
    const onLoadMore = vi.fn();
    const photos = [makePhoto()];
    render(
      <PhotoHistoryPanel {...defaultProps} photos={photos} total={5} hasMore={true} onLoadMore={onLoadMore} />
    );
    fireEvent.click(screen.getByText('Load more'));
    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });

  it('calls onSelectPhoto with the photo id when a photo row is clicked', () => {
    const onSelectPhoto = vi.fn();
    const photos = [makePhoto({ id: 99, original_filename: 'test.png' })];
    render(
      <PhotoHistoryPanel {...defaultProps} photos={photos} total={1} onSelectPhoto={onSelectPhoto} />
    );
    fireEvent.click(screen.getByText('test.png'));
    expect(onSelectPhoto).toHaveBeenCalledWith(99);
  });

  it('highlights the selected history photo', () => {
    const photos = [makePhoto({ id: 99, original_filename: 'selected.png' })];
    render(<PhotoHistoryPanel {...defaultProps} photos={photos} total={1} selectedPhotoId={99} />);

    expect(screen.getByRole('button', { name: /selected\.png/i }).className).toContain(
      'border-accent-blue'
    );
  });

  it('shows "Loading..." when isLoading is true', () => {
    render(<PhotoHistoryPanel {...defaultProps} isLoading={true} />);
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('hides Load more during loading even when hasMore is true', () => {
    const photos = [makePhoto()];
    render(
      <PhotoHistoryPanel {...defaultProps} photos={photos} total={5} hasMore={true} isLoading={true} />
    );
    expect(screen.queryByText('Load more')).toBeNull();
    expect(screen.getByText('Loading...')).toBeDefined();
  });
});
