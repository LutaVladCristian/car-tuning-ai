import type { PhotoStyle } from '../../../types/tuning';

const OPTIONS: { value: PhotoStyle; label: string; icon: string }[] = [
  { value: 'static', label: 'Static display', icon: '📸' },
  { value: 'action', label: 'Action shot', icon: '💨' },
  { value: 'three-quarter', label: '3/4 angle', icon: '🔄' },
  { value: 'dramatic', label: 'Dramatic', icon: '🎬' },
];

interface Props {
  value: PhotoStyle;
  onChange: (v: PhotoStyle) => void;
}

export default function StylePicker({ value, onChange }: Props) {
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
          <span className="text-center leading-tight">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
