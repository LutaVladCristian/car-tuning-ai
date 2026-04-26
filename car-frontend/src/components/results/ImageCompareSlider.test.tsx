import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import ImageCompareSlider from './ImageCompareSlider';

describe('ImageCompareSlider', () => {
  it('renders original and generated images', () => {
    render(<ImageCompareSlider originalUrl="blob:original" resultUrl="blob:generated" />);

    expect(screen.getByAltText('Original car')).toBeDefined();
    expect(screen.getByAltText('Generated car')).toBeDefined();
  });

  it('updates the generated image overlap when the slider moves', () => {
    render(<ImageCompareSlider originalUrl="blob:original" resultUrl="blob:generated" />);

    fireEvent.change(screen.getByLabelText('Compare original and generated image'), {
      target: { value: '25' },
    });

    expect((screen.getByAltText('Generated car') as HTMLImageElement).style.clipPath).toBe(
      'inset(0 0 0 25%)'
    );
  });
});
