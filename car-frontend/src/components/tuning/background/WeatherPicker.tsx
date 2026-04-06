import type { Weather } from '../../../types/tuning';

const OPTIONS: { value: Weather; label: string; icon: string }[] = [
  { value: 'clear', label: 'Clear', icon: '🌤️' },
  { value: 'rain', label: 'Rain', icon: '🌧️' },
  { value: 'snow', label: 'Snow', icon: '❄️' },
  { value: 'fog', label: 'Fog', icon: '🌫️' },
];

interface Props {
  value: Weather;
  onChange: (v: Weather) => void;
}

export default function WeatherPicker({ value, onChange }: Props) {
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
