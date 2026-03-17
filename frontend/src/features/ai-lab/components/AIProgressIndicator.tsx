import type { AIProgressStage } from '../hooks/useAIResearch';

interface AIProgressIndicatorProps {
  stage: AIProgressStage;
  isKo: boolean;
  executionPath?: string | null;
  cacheHit?: boolean | null;
}

const STEP_ORDER: AIProgressStage[] = [
  'interpreting',
  'extracting',
  'loading_data',
  'analyzing',
  'backtesting',
];

function stageLabel(stage: AIProgressStage, isKo: boolean): string {
  const mapKo: Record<AIProgressStage, string> = {
    idle: '대기',
    interpreting: '전략 해석',
    extracting: '파라미터 추출',
    loading_data: '데이터 로딩',
    analyzing: '분석 실행',
    backtesting: '백테스트',
    done: '완료',
    error: '오류',
  };
  const mapEn: Record<AIProgressStage, string> = {
    idle: 'Idle',
    interpreting: 'Interpret',
    extracting: 'Extract',
    loading_data: 'Load Data',
    analyzing: 'Analyze',
    backtesting: 'Backtest',
    done: 'Done',
    error: 'Error',
  };
  return isKo ? mapKo[stage] : mapEn[stage];
}

function activeStepIndex(stage: AIProgressStage): number {
  const idx = STEP_ORDER.indexOf(stage);
  if (idx >= 0) return idx;
  if (stage === 'done') return STEP_ORDER.length - 1;
  if (stage === 'error') return 0;
  return -1;
}

export default function AIProgressIndicator({
  stage,
  isKo,
  executionPath,
  cacheHit,
}: AIProgressIndicatorProps) {
  if (stage === 'idle') return null;
  const activeIndex = activeStepIndex(stage);
  const badge =
    cacheHit === true
      ? (isKo ? '캐시 히트' : 'Cache Hit')
      : cacheHit === false
      ? (isKo ? '신규 계산' : 'Fresh Run')
      : null;

  return (
    <div className="card p-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-dark-300">
          {isKo ? '진행 상태' : 'Progress'}: <span className="text-dark-100">{stageLabel(stage, isKo)}</span>
        </p>
        {badge && <span className="text-[10px] px-2 py-0.5 rounded-full bg-dark-700 text-dark-200 border border-dark-600">{badge}</span>}
      </div>

      <div className="grid grid-cols-5 gap-1">
        {STEP_ORDER.map((step, index) => {
          const done = index <= activeIndex && stage !== 'error';
          const color = done ? 'bg-cyan-400/90' : 'bg-dark-700';
          return (
            <div key={step} className="space-y-1">
              <div className={`h-1.5 rounded-full ${color}`} />
              <p className="text-[10px] text-dark-400 truncate">{stageLabel(step, isKo)}</p>
            </div>
          );
        })}
      </div>

      {executionPath && (
        <p className="text-[10px] text-dark-500 mt-2">
          path: <span className="text-dark-300">{executionPath}</span>
        </p>
      )}
    </div>
  );
}
