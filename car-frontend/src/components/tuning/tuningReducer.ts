import type {
  EditTarget,
  PaintFinish,
  TuningFormState,
} from '../../types/tuning';

export type TuningAction =
  | { type: 'SET_TARGET'; value: EditTarget }
  | { type: 'SET_CAR_COLOR'; value: string }
  | { type: 'SET_CAR_FINISH'; value: PaintFinish }
  | { type: 'SET_CAR_FIELD'; field: string; value: string | null }
  | { type: 'SET_BG_FIELD'; field: string; value: string }
  | { type: 'TOGGLE_BODY_KIT'; value: string }
  | { type: 'TOGGLE_LIGHTING'; value: string }
  | { type: 'SET_CUSTOM_PROMPT'; value: string }
  | { type: 'RESET_PROMPT_OVERRIDE' }
  | { type: 'RESET_FORM' };

export function tuningReducer(state: TuningFormState, action: TuningAction): TuningFormState {
  switch (action.type) {
    case 'SET_TARGET':
      return { ...state, target: action.value, customPromptOverride: null };
    case 'SET_CAR_COLOR':
      return { ...state, car: { ...state.car, color: action.value }, customPromptOverride: null };
    case 'SET_CAR_FINISH':
      return { ...state, car: { ...state.car, finish: action.value }, customPromptOverride: null };
    case 'SET_CAR_FIELD': {
      const key = action.field as keyof typeof state.car;
      return {
        ...state,
        car: { ...state.car, [key]: action.value },
        customPromptOverride: null,
      };
    }
    case 'SET_BG_FIELD': {
      const key = action.field as keyof typeof state.background;
      return {
        ...state,
        background: { ...state.background, [key]: action.value },
        customPromptOverride: null,
      };
    }
    case 'TOGGLE_BODY_KIT': {
      const existing = state.car.bodyKit;
      const next = existing.includes(action.value)
        ? existing.filter((v) => v !== action.value)
        : [...existing, action.value];
      return { ...state, car: { ...state.car, bodyKit: next }, customPromptOverride: null };
    }
    case 'TOGGLE_LIGHTING': {
      const existing = state.car.lighting;
      const next = existing.includes(action.value)
        ? existing.filter((v) => v !== action.value)
        : [...existing, action.value];
      return { ...state, car: { ...state.car, lighting: next }, customPromptOverride: null };
    }
    case 'SET_CUSTOM_PROMPT':
      return { ...state, customPromptOverride: action.value };
    case 'RESET_PROMPT_OVERRIDE':
      return { ...state, customPromptOverride: null };
    case 'RESET_FORM':
      return {
        ...state,
        car: {
          color: '',
          finish: 'solid',
          spoiler: null,
          rimSize: null,
          rimStyle: null,
          rimFinish: null,
          bodyKit: [],
          windowTint: null,
          lighting: [],
          stance: null,
          vinylWrap: null,
        },
        background: { environment: 'urban', timeOfDay: 'sunset', weather: 'clear', style: 'static' },
        customPromptOverride: null,
      };
    default:
      return state;
  }
}
