import type { PaintFinish } from '../../../types/tuning';

const PRESET_COLORS = [
  { name: 'Black', value: 'black', hex: '#1a1a1a' },
  { name: 'White', value: 'pearl white', hex: '#f8f8f0' },
  { name: 'Red', value: 'deep red', hex: '#c0392b' },
  { name: 'Blue', value: 'ocean blue', hex: '#2980b9' },
  { name: 'Racing Green', value: 'racing green', hex: '#1e4d2b' },
  { name: 'Sunset Orange', value: 'sunset orange', hex: '#e67e22' },
  { name: 'Midnight Purple', value: 'midnight purple', hex: '#4a235a' },
  { name: 'Silver', value: 'silver', hex: '#bdc3c7' },
  { name: 'Gunmetal', value: 'gunmetal grey', hex: '#4a4e57' },
  { name: 'Gold', value: 'champagne gold', hex: '#d4ac0d' },
];

const FINISHES: { value: PaintFinish; label: string }[] = [
  { value: 'solid', label: 'Solid' },
  { value: 'metallic', label: 'Metallic' },
  { value: 'matte', label: 'Matte' },
  { value: 'special', label: 'Special' },
];

interface Props {
  color: string;
  finish: PaintFinish;
  onColorChange: (color: string) => void;
  onFinishChange: (finish: PaintFinish) => void;
}

export default function ColorPicker({ color, finish, onColorChange, onFinishChange }: Props) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-5 gap-2">
        {PRESET_COLORS.map((c) => (
          <button
            key={c.value}
            type="button"
            title={c.name}
            onClick={() => onColorChange(c.value)}
            className={`h-8 rounded-md transition-all border-2 ${
              color === c.value ? 'border-accent-blue scale-110' : 'border-transparent hover:border-zinc-500'
            }`}
            style={{ backgroundColor: c.hex }}
          />
        ))}
      </div>

      <div className="flex items-center gap-2">
        <input
          type="text"
          value={color}
          onChange={(e) => onColorChange(e.target.value)}
          placeholder="e.g. midnight blue, candy red..."
          className="flex-1 bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-zinc-100 placeholder-zinc-600 text-xs focus:outline-none focus:border-accent-blue"
        />
      </div>

      <div className="flex gap-2">
        {FINISHES.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => onFinishChange(f.value)}
            className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
              finish === f.value
                ? 'bg-accent-blue text-white'
                : 'bg-surface-700 text-zinc-400 hover:text-zinc-200 border border-surface-600'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  );
}
