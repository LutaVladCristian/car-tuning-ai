import type { CarEditState } from '../../../types/tuning';
import type { Dispatch } from 'react';
import type { TuningAction } from '../tuningReducer';

const SPOILERS = ['None', 'Low-profile lip', 'Sport spoiler', 'Performance wing', 'GT racing wing'];
const RIM_SIZES = ['Stock', '17-inch', '18-inch', '19-inch', '20-inch', '21-inch'];
const RIM_STYLES = ['Multi-spoke', '5-spoke', 'Mesh', 'Split', 'Deep dish', 'Forged monoblock'];
const RIM_FINISHES = ['Chrome', 'Matte black', 'Bronze', 'Gold', 'Gunmetal', 'Polished silver'];
const BODY_KITS = ['Front bumper sport', 'Rear bumper diffuser', 'Side skirts', 'Fender flares', 'Hood scoop', 'Wide body kit'];
const STANCES = ['Stock', 'Lowered (-30mm)', 'Lowered (-50mm)', 'Stanced wide fitment'];

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
  options,
  value,
  onSelect,
}: {
  options: string[];
  value: string | null;
  onSelect: (v: string | null) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const isNone = opt === 'None' || opt === 'Stock';
        const active = isNone ? value === null : value === opt;
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onSelect(isNone ? null : opt)}
            className={`px-3 py-1 rounded-full text-xs transition-colors ${
              active
                ? 'bg-accent-blue text-white'
                : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
            }`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

function CheckGroup({
  options,
  selected,
  onToggle,
}: {
  options: string[];
  selected: string[];
  onToggle: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onToggle(opt)}
          className={`px-3 py-1 rounded-full text-xs transition-colors ${
            selected.includes(opt)
              ? 'bg-accent-blue text-white'
              : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export default function BodyModPanel({ car, dispatch }: Props) {
  return (
    <div className="space-y-4">
      <Section title="Spoiler">
        <PillGroup
          options={SPOILERS}
          value={car.spoiler}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'spoiler', value: v })}
        />
      </Section>

      <Section title="Rim size">
        <PillGroup
          options={RIM_SIZES}
          value={car.rimSize}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'rimSize', value: v })}
        />
      </Section>

      <Section title="Rim style">
        <PillGroup
          options={RIM_STYLES}
          value={car.rimStyle}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'rimStyle', value: v })}
        />
      </Section>

      <Section title="Rim finish">
        <PillGroup
          options={RIM_FINISHES}
          value={car.rimFinish}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'rimFinish', value: v })}
        />
      </Section>

      <Section title="Body kit (multi-select)">
        <CheckGroup
          options={BODY_KITS}
          selected={car.bodyKit}
          onToggle={(v) => dispatch({ type: 'TOGGLE_BODY_KIT', value: v })}
        />
      </Section>

      <Section title="Stance">
        <PillGroup
          options={STANCES}
          value={car.stance}
          onSelect={(v) => dispatch({ type: 'SET_CAR_FIELD', field: 'stance', value: v })}
        />
      </Section>
    </div>
  );
}
