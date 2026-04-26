import { useState } from 'react';

interface Props {
  originalUrl: string;
  resultUrl: string;
}

export default function ImageCompareSlider({ originalUrl, resultUrl }: Props) {
  const [position, setPosition] = useState(50);
  const generatedClip = `inset(0 0 0 ${position}%)`;

  return (
    <div className="space-y-3">
      <div className="relative w-full overflow-hidden rounded-lg border border-surface-600 bg-surface-900 aspect-[4/3] max-h-[62vh] select-none">
        <img
          src={originalUrl}
          alt="Original car"
          className="absolute inset-0 h-full w-full object-contain"
          draggable={false}
        />
        <img
          src={resultUrl}
          alt="Generated car"
          className="absolute inset-0 h-full w-full object-contain"
          style={{ clipPath: generatedClip }}
          draggable={false}
        />

        <div className="pointer-events-none absolute inset-x-3 top-3 flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-white">
          <span className="rounded bg-black/60 px-2 py-1">Original</span>
          <span className="rounded bg-black/60 px-2 py-1">Generated</span>
        </div>

        <div
          className="pointer-events-none absolute top-0 h-full w-0.5 bg-white shadow-[0_0_0_1px_rgba(0,0,0,0.35)]"
          style={{ left: `${position}%` }}
        />
        <div
          className="pointer-events-none absolute top-1/2 h-9 w-9 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/80 bg-black/60 shadow-lg"
          style={{ left: `${position}%` }}
          aria-hidden="true"
        >
          <span className="absolute left-2 top-1/2 h-2 w-2 -translate-y-1/2 rotate-45 border-b border-l border-white" />
          <span className="absolute right-2 top-1/2 h-2 w-2 -translate-y-1/2 rotate-45 border-r border-t border-white" />
        </div>

        <input
          aria-label="Compare original and generated image"
          type="range"
          min="0"
          max="100"
          value={position}
          onChange={(event) => setPosition(Number(event.target.value))}
          className="absolute inset-0 h-full w-full cursor-ew-resize opacity-0"
        />
      </div>

      <input
        aria-hidden="true"
        tabIndex={-1}
        type="range"
        min="0"
        max="100"
        value={position}
        onChange={(event) => setPosition(Number(event.target.value))}
        className="h-2 w-full cursor-ew-resize appearance-none rounded-full bg-surface-600 accent-accent-blue"
      />
    </div>
  );
}
