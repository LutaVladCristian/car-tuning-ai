import type { CarEditState } from '../../../types/tuning';
import type { Dispatch } from 'react';
import type { TuningAction } from '../TuningForm';

const WINDOW_TINTS = ['None', '70% (light)', '50% (medium)', '35% (dark)', '20% (very dark)', '5% (limo)'];
const LIGHTING = [
  'LED headlights', 'Halo angel eyes', 'RGB underbody strips',
  'Smoked headlights', 'Sequential LED taillights', 'Color-matched DRL',
];
const VINYL_WRAPS = ['None', 'Racing stripes', 'Dual racing stripes', 'Flames', 'Geometric pattern', 'Carbon fiber hood'];

interface Props {
  car: CarEditState;
  dispatch: Dispatch<TuningAction>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">{title}</p>
      {children}
    </div>
  );
}

function PillGroup({
  options, value, onSelect,
}: { options: string[]; value: string | null; onSelect: (v: string | null) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const isNone = opt === 'None';
        const active = isNone ? value === null : value === opt;
        return (
          <button key={opt} type="button" onClick={() => onSelect(isNone ? null : opt)}
            className={`px-3 py-1 rounded-full text-xs transition-colors ${
              active ? 'bg-accent-blue text-white' : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
            }`}>
            {opt}
          </button>
        );
      })}
    </div>
  );
}

function CheckGroup({
  options, selected, onToggle,
}: { options: string[]; selected: string[]; onToggle: (v: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => (
        <button key={opt} type="button" onClick={() => onToggle(opt)}
          className={`px-3 py-1 rounded-full text-xs transition-colors ${
            selected.includes(opt) ? 'bg-accent-blue text-white' : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
          }`}>
          {opt}
        </button>
      ))}
    </div>
  );
}

export default function CosmeticPanel({ car, dispatch }: Props) {
  return (
    <div className="space-y-4">
      <Section title="Window tint">
        <PillGroup
          options={WINDOW_TINTS}
          value={car.windowTint}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'windowTint', value: v })}
        />
      </Section>

      <Section title="Lighting upgrades (multi-select)">
        <CheckGroup
          options={LIGHTING}
          selected={car.lighting}
          onToggle={(v) => dispatch({ type: 'TOGGLE_LIGHTING', value: v })}
        />
      </Section>

      <Section title="Vinyl wrap / graphics">
        <PillGroup
          options={VINYL_WRAPS}
          value={car.vinylWrap}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'vinylWrap', value: v })}
        />
      </Section>
    </div>
  );
}
