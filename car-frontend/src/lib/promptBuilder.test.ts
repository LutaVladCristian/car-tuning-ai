import { describe, expect, it } from 'vitest';
import { DEFAULT_FORM_STATE, type TuningFormState } from '../types/tuning';
import { buildPrompt } from './promptBuilder';

function makeState(overrides: Partial<TuningFormState> = {}): TuningFormState {
  return {
    ...DEFAULT_FORM_STATE,
    car: { ...DEFAULT_FORM_STATE.car },
    background: { ...DEFAULT_FORM_STATE.background },
    ...overrides,
  };
}

describe('buildPrompt', () => {
  it('returns the custom prompt override when one is set', () => {
    const prompt = buildPrompt(makeState({ customPromptOverride: 'make it rally-ready' }));

    expect(prompt).toBe('make it rally-ready');
  });

  it('builds a car edit prompt from selected tuning options', () => {
    const prompt = buildPrompt(
      makeState({
        target: 'car',
        car: {
          ...DEFAULT_FORM_STATE.car,
          color: 'racing green',
          finish: 'metallic',
          spoiler: 'GT racing',
          rimSize: '19-inch',
          rimStyle: 'mesh design',
          rimFinish: 'bronze',
          bodyKit: ['front splitter', 'side skirts'],
          lighting: ['halo headlights'],
        },
      })
    );

    expect(prompt).toContain('metallic racing green paint');
    expect(prompt).toContain('Add a GT racing spoiler');
    expect(prompt).toContain('Fit 19-inch mesh design wheels with bronze finish');
    expect(prompt).toContain('Apply body kit: front splitter, side skirts');
    expect(prompt).toContain('Upgrade lighting with: halo headlights');
    expect(prompt).toContain('Use the provided mask to restrict changes to the car body only');
  });

  it('returns the default enhancement prompt when no car options are set', () => {
    const prompt = buildPrompt(makeState({ target: 'car' }));
    expect(prompt).toContain('Enhance the car in this photograph with photorealistic quality');
    expect(prompt).toContain('Use the provided mask to restrict changes to the car body only');
    expect(prompt).not.toContain('Repaint');
  });

  it('builds a car prompt with only color and finish set', () => {
    const prompt = buildPrompt(
      makeState({ target: 'car', car: { ...DEFAULT_FORM_STATE.car, color: 'pearl white', finish: 'special' } })
    );
    expect(prompt).toContain('special-effect pearl white paint');
    expect(prompt).not.toContain('spoiler');
    expect(prompt).not.toContain('body kit');
  });

  it('builds a car prompt with only cosmetics set (no color or body mods)', () => {
    const prompt = buildPrompt(
      makeState({
        target: 'car',
        car: {
          ...DEFAULT_FORM_STATE.car,
          windowTint: '20% limo tint',
          lighting: ['LED strips', 'halo headlights'],
          vinylWrap: 'carbon fibre',
        },
      })
    );
    expect(prompt).toContain('20% limo tint window tint');
    expect(prompt).toContain('LED strips, halo headlights');
    expect(prompt).toContain('carbon fibre vinyl wrap');
    expect(prompt).not.toContain('Repaint');
  });

  it('omits rim finish from the prompt when rimFinish is null', () => {
    const prompt = buildPrompt(
      makeState({
        target: 'car',
        car: { ...DEFAULT_FORM_STATE.car, rimSize: '18-inch', rimStyle: 'split-spoke', rimFinish: null },
      })
    );
    expect(prompt).toContain('18-inch split-spoke wheels');
    expect(prompt).not.toContain('with null finish');
  });

  it('builds the default background prompt using default scene options', () => {
    // DEFAULT_BACKGROUND_STATE: urban / sunset / clear / static
    const prompt = buildPrompt(makeState({ target: 'background' }));
    expect(prompt).toContain('photorealistic urban city street');
    expect(prompt).toContain('golden hour sunset');
    expect(prompt).toContain('clear sky');
    expect(prompt).toContain('clean static display environment');
    expect(prompt).toContain('Keep the car exactly as it is');
    expect(prompt).toContain('car bounding box, car scale, and car position');
  });

  it('builds a background replacement prompt from scene settings', () => {
    const prompt = buildPrompt(
      makeState({
        target: 'background',
        background: {
          environment: 'mountain',
          timeOfDay: 'night',
          weather: 'fog',
          style: 'dramatic',
        },
      })
    );

    expect(prompt).toContain('scenic mountain road');
    expect(prompt).toContain('nighttime with city lights');
    expect(prompt).toContain('dense atmospheric fog');
    expect(prompt).toContain('dramatic cinematic lighting with stronger contrast');
    expect(prompt).not.toContain('low-angle');
    expect(prompt).toContain('Keep the car exactly as it is');
  });
});
