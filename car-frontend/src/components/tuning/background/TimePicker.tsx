import type { TimeOfDay } from '../../../types/tuning';

const OPTIONS: { value: TimeOfDay; label: string; icon: string }[] = [
  { value: 'day', label: 'Midday', icon: '☀️' },
  { value: 'sunset', label: 'Sunset', icon: '🌅' },
  { value: 'night', label: 'Night', icon: '🌃' },
  { value: 'dawn', label: 'Dawn', icon: '🌄' },
];

interface Props {
  value: TimeOfDay;
  onChange: (v: TimeOfDay) => void;
}

export default function TimePicker({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={`flex-1 flex flex-col items-center gap-1 py-2.5 rounded-lg text-xs transition-all border ${
            value === opt.value
              ? 'border-accent-orange bg-accent-orange/10 text-accent-orange'
              : 'border-surface-600 bg-surface-700 text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <span className="text-lg">{opt.icon}</span>
          <span>{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
