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
    expect(prompt).toContain('dramatic low-angle cinematic composition');
    expect(prompt).toContain('Keep the car exactly as it is');
  });
});
