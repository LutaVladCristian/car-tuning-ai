import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import TuningPage from './TuningPage';

vi.mock('../hooks/usePhotoHistory', () => ({
  usePhotoHistory: () => ({
    photos: [
      {
        id: 123,
        user_id: 1,
        original_filename: 'history-car.png',
        operation_type: 'edit_photo',
        operation_params: null,
        created_at: '2026-04-14T12:00:00Z',
      },
    ],
    total: 1,
    isLoading: false,
    hasMore: false,
    refetch: vi.fn(),
    fetchMore: vi.fn(),
  }),
}));

vi.mock('../hooks/useEditPhoto', () => ({
  useEditPhoto: () => ({
    status: 'idle',
    resultPhotoId: null,
    error: null,
    submit: vi.fn(),
    reset: vi.fn(),
  }),
}));

vi.mock('../api/photos', () => ({
  getPhotoBlob: vi.fn(),
}));

vi.mock('../components/tuning/ImageSelector', () => ({
  default: () => <div>Image selector</div>,
}));

vi.mock('../components/tuning/TuningForm', () => ({
  default: () => <div>Tuning form</div>,
}));

vi.mock('../components/prompt/PromptPreview', () => ({
  default: () => <div>Prompt preview</div>,
}));

vi.mock('../components/results/ResultDisplay', () => ({
  default: ({ activePhotoId }: { activePhotoId: number | null }) => (
    <div>active comparison: {activePhotoId ?? 'none'}</div>
  ),
}));

vi.mock('../components/results/PhotoHistoryPanel', () => ({
  default: ({ onSelectPhoto }: { onSelectPhoto: (id: number) => void }) => (
    <button type="button" onClick={() => onSelectPhoto(123)}>
      Select history photo
    </button>
  ),
}));

describe('TuningPage', () => {
  it('loads a selected history photo into the comparison result section', () => {
    render(<TuningPage />);

    expect(screen.getByText('active comparison: none')).toBeDefined();
    fireEvent.click(screen.getByText('Select history photo'));
    expect(screen.getByText('active comparison: 123')).toBeDefined();
  });
});
