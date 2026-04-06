import type { EditTarget } from '../../types/tuning';

interface Props {
  value: EditTarget;
  onChange: (t: EditTarget) => void;
}

export default function TargetSelector({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={() => onChange('car')}
        className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
          value === 'car'
            ? 'bg-accent-blue text-white shadow-glow-blue'
            : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
        }`}
      >
        Edit Car
      </button>
      <button
        type="button"
        onClick={() => onChange('background')}
        className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
          value === 'background'
            ? 'bg-accent-orange text-white shadow-glow-orange'
            : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
        }`}
      >
        Edit Background
      </button>
    </div>
  );
}
