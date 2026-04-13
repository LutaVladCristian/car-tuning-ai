import type { Dispatch } from 'react';
import type { TuningFormState } from '../../types/tuning';
import type { TuningAction } from './tuningReducer';
import TargetSelector from './TargetSelector';
import ColorPicker from './car/ColorPicker';
import BodyModPanel from './car/BodyModPanel';
import CosmeticPanel from './car/CosmeticPanel';
import EnvironmentPicker from './background/EnvironmentPicker';
import TimePicker from './background/TimePicker';
import WeatherPicker from './background/WeatherPicker';
import StylePicker from './background/StylePicker';

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
