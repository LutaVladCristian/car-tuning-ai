interface Props {
  prompt: string;
  isOverridden: boolean;
  onChange: (value: string) => void;
  onReset: () => void;
}

export default function PromptPreview({ prompt, isOverridden, onChange, onReset }: Props) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          AI Prompt
        </span>
        <div className="flex items-center gap-2">
          {isOverridden && (
            <span className="text-xs bg-accent-orange/20 text-accent-orange px-2 py-0.5 rounded-full">
              Custom
            </span>
          )}
          {isOverridden && (
            <button
              type="button"
              onClick={onReset}
              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Reset to auto
            </button>
          )}
        </div>
      </div>
      <textarea
        value={prompt}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        className="w-full bg-surface-700 border border-surface-600 rounded-lg px-4 py-3 text-zinc-300 font-mono text-xs resize-y focus:outline-none focus:border-accent-blue transition-colors leading-relaxed"
        placeholder="Select options above to generate a prompt..."
      />
      <p className="text-zinc-600 text-xs">
        Edit freely — or reset to let selections rebuild it automatically.
      </p>
    </div>
  );
}
