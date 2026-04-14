import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { fireEvent } from '@testing-library/react';
import ResultDisplay from './ResultDisplay';

vi.mock('../../api/photos', () => ({
  getPhotoUrl: vi.fn(),
}));

import { getPhotoUrl } from '../../api/photos';
const mockGetPhotoUrl = vi.mocked(getPhotoUrl);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ResultDisplay', () => {
  it('renders the idle placeholder when status is idle', () => {
    render(
      <ResultDisplay status="idle" resultPhotoId={null} error={null} onReset={vi.fn()} />
    );
    expect(screen.getByText('Your result will appear here')).toBeDefined();
  });

  it('renders the submitting spinner when status is submitting', () => {
    render(
      <ResultDisplay status="submitting" resultPhotoId={null} error={null} onReset={vi.fn()} />
    );
    expect(screen.getByText('Sending to AI...')).toBeDefined();
    expect(screen.getByText('OpenAI is processing your image')).toBeDefined();
  });

  it('renders the polling spinner when status is polling', () => {
    render(
      <ResultDisplay status="polling" resultPhotoId={null} error={null} onReset={vi.fn()} />
    );
    expect(screen.getByText('Saving result...')).toBeDefined();
    expect(screen.getByText('Finalizing your photo record')).toBeDefined();
  });

  it('renders the error message and Try again button when status is error', () => {
    render(
      <ResultDisplay status="error" resultPhotoId={null} error="Request timed out" onReset={vi.fn()} />
    );
    expect(screen.getByText('Something went wrong')).toBeDefined();
    expect(screen.getByText('Request timed out')).toBeDefined();
    expect(screen.getByText('Try again')).toBeDefined();
  });

  it('calls onReset when the Try again button is clicked', () => {
    const onReset = vi.fn();
    render(
      <ResultDisplay status="error" resultPhotoId={null} error="Oops" onReset={onReset} />
    );
    fireEvent.click(screen.getByText('Try again'));
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it('renders the result image after fetching the URL on success', async () => {
    mockGetPhotoUrl.mockResolvedValueOnce('blob:http://localhost/fake-url');

    render(
      <ResultDisplay status="success" resultPhotoId={42} error={null} onReset={vi.fn()} />
    );

    const img = await waitFor(() => screen.getByAltText('Edited car'));
    expect(img).toBeDefined();
    expect((img as HTMLImageElement).src).toContain('blob:');
    expect(mockGetPhotoUrl).toHaveBeenCalledWith(42);
  });

  it('shows the history fallback message when success has no resultPhotoId', () => {
    render(
      <ResultDisplay status="success" resultPhotoId={null} error={null} onReset={vi.fn()} />
    );
    expect(screen.getByText(/Check your photo history/)).toBeDefined();
    expect(mockGetPhotoUrl).not.toHaveBeenCalled();
  });

  it('calls onReset when the New edit button is clicked on success', async () => {
    const onReset = vi.fn();
    mockGetPhotoUrl.mockResolvedValueOnce('blob:http://localhost/fake-url');

    render(
      <ResultDisplay status="success" resultPhotoId={1} error={null} onReset={onReset} />
    );

    await waitFor(() => screen.getByAltText('Edited car'));
    fireEvent.click(screen.getByText('New edit'));
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
