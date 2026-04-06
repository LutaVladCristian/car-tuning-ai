import type { Dispatch } from 'react';
import type {
  TuningFormState,
  EditTarget,
  PaintFinish,
} from '../../types/tuning';
import TargetSelector from './TargetSelector';
import ColorPicker from './car/ColorPicker';
import BodyModPanel from './car/BodyModPanel';
import CosmeticPanel from './car/CosmeticPanel';
import EnvironmentPicker from './background/EnvironmentPicker';
import TimePicker from './background/TimePicker';
import WeatherPicker from './background/WeatherPicker';
import StylePicker from './background/StylePicker';

// All actions that can mutate TuningFormState
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
          color: '', finish: 'solid', spoiler: null, rimSize: null,
          rimStyle: null, rimFinish: null, bodyKit: [], windowTint: null,
          lighting: [], stance: null, vinylWrap: null,
        },
        background: { environment: 'urban', timeOfDay: 'sunset', weather: 'clear', style: 'static' },
        customPromptOverride: null,
      };
    default:
      return state;
  }
}

interface SectionProps {
  title: string;
  accent?: 'blue' | 'orange';
  children: React.ReactNode;
}

function Section({ title, accent = 'blue', children }: SectionProps) {
  return (
    <div className="space-y-3">
      <h3 className={`text-xs font-semibold uppercase tracking-widest ${
        accent === 'blue' ? 'text-accent-blue' : 'text-accent-orange'
      }`}>
        {title}
      </h3>
      {children}
    </div>
  );
}

interface Props {
  formState: TuningFormState;
  dispatch: Dispatch<TuningAction>;
}

export default function TuningForm({ formState, dispatch }: Props) {
  const accent = formState.target === 'car' ? 'blue' : 'orange';

  return (
    <div className="space-y-5">
      <TargetSelector
        value={formState.target}
        onChange={(v) => dispatch({ type: 'SET_TARGET', value: v })}
      />

      {formState.target === 'car' ? (
        <>
          <Section title="Paint & finish" accent={accent}>
            <ColorPicker
              color={formState.car.color}
              finish={formState.car.finish}
              onColorChange={(v) => dispatch({ type: 'SET_CAR_COLOR', value: v })}
              onFinishChange={(v) => dispatch({ type: 'SET_CAR_FINISH', value: v })}
            />
          </Section>

          <Section title="Body modifications" accent={accent}>
            <BodyModPanel car={formState.car} dispatch={dispatch} />
          </Section>

          <Section title="Cosmetics" accent={accent}>
            <CosmeticPanel car={formState.car} dispatch={dispatch} />
          </Section>
        </>
      ) : (
        <>
          <Section title="Environment" accent={accent}>
            <EnvironmentPicker
              value={formState.background.environment}
              onChange={(v) => dispatch({ type: 'SET_BG_FIELD', field: 'environment', value: v })}
            />
          </Section>

          <Section title="Time of day" accent={accent}>
            <TimePicker
              value={formState.background.timeOfDay}
              onChange={(v) => dispatch({ type: 'SET_BG_FIELD', field: 'timeOfDay', value: v })}
            />
          </Section>

          <Section title="Weather" accent={accent}>
            <WeatherPicker
              value={formState.background.weather}
              onChange={(v) => dispatch({ type: 'SET_BG_FIELD', field: 'weather', value: v })}
            />
          </Section>

          <Section title="Photography style" accent={accent}>
            <StylePicker
              value={formState.background.style}
              onChange={(v) => dispatch({ type: 'SET_BG_FIELD', field: 'style', value: v })}
            />
          </Section>
        </>
      )}
    </div>
  );
}
