interface Props {
  prompt: string;
}

export default function PromptPreview({ prompt }: Props) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          AI Prompt
        </span>
      </div>
      <textarea
        value={prompt}
        readOnly
        rows={4}
        maxLength={1000}
        className="w-full bg-surface-700 border border-surface-600 rounded-lg px-4 py-3 text-zinc-300 font-mono text-xs resize-y focus:outline-none focus:border-surface-600 leading-relaxed cursor-default"
        placeholder="Select options above to generate a prompt..."
      />
      <div className="flex justify-between">
        <p className="text-zinc-600 text-xs">Generated from your selected options.</p>
        <p className={`text-xs ${prompt.length >= 950 ? 'text-accent-orange' : 'text-zinc-600'}`}>
          {prompt.length}/1000
        </p>
      </div>
    </div>
  );
}
