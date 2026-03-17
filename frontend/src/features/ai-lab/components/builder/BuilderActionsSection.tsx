import { AlertTriangle, FlaskConical, Loader2, Wand2 } from 'lucide-react';

interface BuilderActionsSectionProps {
  isKo: boolean;
  directionDisabled: boolean;
  isGenerating: boolean;
  isRunning: boolean;
  runError: string | null;
  onGenerateDraft: () => void;
  onRunBacktest: () => void;
}

export default function BuilderActionsSection({
  isKo,
  directionDisabled,
  isGenerating,
  isRunning,
  runError,
  onGenerateDraft,
  onRunBacktest,
}: BuilderActionsSectionProps) {
  return (
    <>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={onGenerateDraft}
          className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
          disabled={isGenerating}
        >
          {isGenerating ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Wand2 className="w-4 h-4" />
          )}
          {isKo ? '전략 초안 생성' : 'Generate Draft'}
        </button>
        <button
          className="btn bg-dark-700 hover:bg-dark-600 text-dark-200 border border-dark-600 flex items-center gap-2 disabled:opacity-50"
          onClick={onRunBacktest}
          disabled={isRunning || isGenerating || directionDisabled}
          title={
            directionDisabled
              ? isKo
                ? 'Long/Short 중 하나 선택'
                : 'Pick Long or Short'
              : ''
          }
        >
          {isRunning ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FlaskConical className="w-4 h-4" />
          )}
          {isKo ? '초안으로 백테스트 실행' : 'Run Backtest from Draft'}
        </button>
      </div>

      {runError ? (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-300 text-sm px-3 py-2 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {runError}
        </div>
      ) : null}
    </>
  );
}
