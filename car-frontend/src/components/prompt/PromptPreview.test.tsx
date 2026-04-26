import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import PromptPreview from './PromptPreview';

describe('PromptPreview', () => {
  it('renders the current prompt value in the textarea', () => {
    render(<PromptPreview prompt="make it red" />);

    expect((screen.getByRole('textbox') as HTMLTextAreaElement).value).toBe('make it red');
  });

  it('renders the textarea as read-only', () => {
    render(<PromptPreview prompt="auto-generated" />);

    expect((screen.getByRole('textbox') as HTMLTextAreaElement).readOnly).toBe(true);
  });

  it('does not change the prompt when typing is attempted', () => {
    render(<PromptPreview prompt="locked prompt" />);

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'manual edit' } });

    expect((screen.getByRole('textbox') as HTMLTextAreaElement).value).toBe('locked prompt');
  });

  it('shows the character count', () => {
    render(<PromptPreview prompt="12345" />);

    expect(screen.getByText('5/1000')).toBeDefined();
  });
});
