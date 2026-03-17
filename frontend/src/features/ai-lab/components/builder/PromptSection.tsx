interface PromptSectionProps {
  isKo: boolean;
  prompt: string;
  promptSamples: string[];
  onPromptChange: (value: string) => void;
  onPromptSampleSelect: (sample: string) => void;
}

export default function PromptSection({
  isKo,
  prompt,
  promptSamples,
  onPromptChange,
  onPromptSampleSelect,
}: PromptSectionProps) {
  return (
    <>
      <div>
        <label className="block text-sm text-dark-300 mb-2">
          {isKo ? 'AI 요청 프롬프트' : 'AI Prompt'}
        </label>
        <textarea
          className="w-full min-h-[120px] bg-dark-800 border border-dark-600 rounded-lg p-3 text-sm"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder={
            isKo
              ? '예: RSI 과매도 반등 + SMA 돌파 조합을 찾고 TP/SL도 포함해줘'
              : 'e.g. Build RSI oversold rebound + SMA breakout strategy with TP/SL'
          }
        />
      </div>

      <div>
        <div className="text-xs text-dark-400 mb-2 uppercase tracking-wide">
          {isKo ? '빠른 예시' : 'Quick Samples'}
        </div>
        <div className="flex flex-wrap gap-2">
          {promptSamples.map((sample) => (
            <button
              key={sample}
              onClick={() => onPromptSampleSelect(sample)}
              className="px-3 py-1.5 rounded-lg text-xs bg-dark-700 hover:bg-dark-600 text-dark-200"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
