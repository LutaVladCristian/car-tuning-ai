import type { Environment } from '../../../types/tuning';

const OPTIONS: { value: Environment; label: string; icon: string }[] = [
  { value: 'urban', label: 'Urban City', icon: '🏙️' },
  { value: 'mountain', label: 'Mountain Road', icon: '⛰️' },
  { value: 'track', label: 'Race Track', icon: '🏁' },
  { value: 'beach', label: 'Beach Road', icon: '🏖️' },
  { value: 'industrial', label: 'Industrial', icon: '🏭' },
];

interface Props {
  value: Environment;
  onChange: (v: Environment) => void;
}

export default function EnvironmentPicker({ value, onChange }: Props) {
  return (
    <div className="grid grid-cols-5 gap-2">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={`flex flex-col items-center gap-1 py-3 rounded-lg text-xs transition-all border ${
            value === opt.value
              ? 'border-accent-orange bg-accent-orange/10 text-accent-orange'
              : 'border-surface-600 bg-surface-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-500'
          }`}
        >
          <span className="text-xl">{opt.icon}</span>
          <span className="leading-tight text-center">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
