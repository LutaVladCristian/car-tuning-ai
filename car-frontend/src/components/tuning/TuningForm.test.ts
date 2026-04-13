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
});
