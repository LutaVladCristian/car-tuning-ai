import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PromptPreview from './PromptPreview';

describe('PromptPreview', () => {
  it('renders the current prompt value in the textarea', () => {
    render(
      <PromptPreview
        prompt="make it red"
        isOverridden={false}
        onChange={vi.fn()}
        onReset={vi.fn()}
      />
    );
    expect((screen.getByRole('textbox') as HTMLTextAreaElement).value).toBe('make it red');
  });

  it('shows the Custom badge and Reset button when overridden', () => {
    render(
      <PromptPreview
        prompt="custom"
        isOverridden={true}
        onChange={vi.fn()}
        onReset={vi.fn()}
      />
    );
    expect(screen.getByText('Custom')).toBeDefined();
    expect(screen.getByText('Reset to auto')).toBeDefined();
  });

  it('hides the Custom badge and Reset button when not overridden', () => {
    render(
      <PromptPreview
        prompt="auto-generated"
        isOverridden={false}
        onChange={vi.fn()}
        onReset={vi.fn()}
      />
    );
    expect(screen.queryByText('Custom')).toBeNull();
    expect(screen.queryByText('Reset to auto')).toBeNull();
  });

  it('calls onChange with the new value when the textarea is edited', () => {
    const onChange = vi.fn();
    render(
      <PromptPreview prompt="" isOverridden={false} onChange={onChange} onReset={vi.fn()} />
    );
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'new prompt text' } });
    expect(onChange).toHaveBeenCalledWith('new prompt text');
  });

  it('calls onReset when the Reset button is clicked', () => {
    const onReset = vi.fn();
    render(
      <PromptPreview prompt="custom" isOverridden={true} onChange={vi.fn()} onReset={onReset} />
    );
    fireEvent.click(screen.getByText('Reset to auto'));
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
