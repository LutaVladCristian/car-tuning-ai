import { describe, expect, it } from 'vitest';
import { DEFAULT_FORM_STATE, type TuningFormState } from '../../types/tuning';
import { tuningReducer } from './tuningReducer';

function makeState(overrides: Partial<TuningFormState> = {}): TuningFormState {
  return {
    ...DEFAULT_FORM_STATE,
    car: { ...DEFAULT_FORM_STATE.car },
    background: { ...DEFAULT_FORM_STATE.background },
    ...overrides,
  };
}

describe('tuningReducer', () => {
  it('clears custom prompt overrides when changing target', () => {
    const next = tuningReducer(
      makeState({ customPromptOverride: 'custom prompt' }),
      { type: 'SET_TARGET', value: 'car' }
    );

    expect(next.target).toBe('car');
    expect(next.customPromptOverride).toBeNull();
  });

  it('toggles body kit selections without mutating existing state', () => {
    const initial = makeState({
      car: { ...DEFAULT_FORM_STATE.car, bodyKit: ['front splitter'] },
    });

    const added = tuningReducer(initial, { type: 'TOGGLE_BODY_KIT', value: 'side skirts' });
    const removed = tuningReducer(added, { type: 'TOGGLE_BODY_KIT', value: 'front splitter' });

    expect(initial.car.bodyKit).toEqual(['front splitter']);
    expect(added.car.bodyKit).toEqual(['front splitter', 'side skirts']);
    expect(removed.car.bodyKit).toEqual(['side skirts']);
  });

  it('resets form options while preserving the selected target', () => {
    const next = tuningReducer(
      makeState({
        target: 'car',
        car: {
          ...DEFAULT_FORM_STATE.car,
          color: 'red',
          bodyKit: ['wide body'],
        },
        customPromptOverride: 'custom prompt',
      }),
      { type: 'RESET_FORM' }
    );

    expect(next.target).toBe('car');
    expect(next.car).toEqual(DEFAULT_FORM_STATE.car);
    expect(next.background).toEqual(DEFAULT_FORM_STATE.background);
    expect(next.customPromptOverride).toBeNull();
  });

  it('sets car color and clears custom prompt override', () => {
    const next = tuningReducer(
      makeState({ customPromptOverride: 'old prompt' }),
      { type: 'SET_CAR_COLOR', value: 'midnight blue' }
    );

    expect(next.car.color).toBe('midnight blue');
    expect(next.customPromptOverride).toBeNull();
  });

  it('sets car finish and clears custom prompt override', () => {
    const next = tuningReducer(
      makeState({ customPromptOverride: 'old prompt' }),
      { type: 'SET_CAR_FINISH', value: 'matte' }
    );

    expect(next.car.finish).toBe('matte');
    expect(next.customPromptOverride).toBeNull();
  });

  it('sets an arbitrary car field and clears custom prompt override', () => {
    const next = tuningReducer(
      makeState({ customPromptOverride: 'old prompt' }),
      { type: 'SET_CAR_FIELD', field: 'spoiler', value: 'GT wing' }
    );

    expect(next.car.spoiler).toBe('GT wing');
    expect(next.customPromptOverride).toBeNull();
  });

  it('sets a background field and clears custom prompt override', () => {
    const next = tuningReducer(
      makeState({ customPromptOverride: 'old prompt' }),
      { type: 'SET_BG_FIELD', field: 'timeOfDay', value: 'night' }
    );

    expect(next.background.timeOfDay).toBe('night');
    expect(next.customPromptOverride).toBeNull();
  });

  it('toggles lighting selections without mutating existing state', () => {
    const initial = makeState({
      car: { ...DEFAULT_FORM_STATE.car, lighting: ['halo headlights'] },
    });

    const added = tuningReducer(initial, { type: 'TOGGLE_LIGHTING', value: 'underglow' });
    const removed = tuningReducer(added, { type: 'TOGGLE_LIGHTING', value: 'halo headlights' });

    expect(initial.car.lighting).toEqual(['halo headlights']);
    expect(added.car.lighting).toEqual(['halo headlights', 'underglow']);
    expect(removed.car.lighting).toEqual(['underglow']);
  });

  it('sets custom prompt override without clearing it', () => {
    const next = tuningReducer(
      makeState(),
      { type: 'SET_CUSTOM_PROMPT', value: 'make it aggressive' }
    );

    expect(next.customPromptOverride).toBe('make it aggressive');
  });

  it('clears only the custom prompt override on RESET_PROMPT_OVERRIDE', () => {
    const initial = makeState({
      car: { ...DEFAULT_FORM_STATE.car, color: 'red' },
      customPromptOverride: 'some prompt',
    });

    const next = tuningReducer(initial, { type: 'RESET_PROMPT_OVERRIDE' });

    expect(next.customPromptOverride).toBeNull();
    expect(next.car.color).toBe('red');
  });
});
