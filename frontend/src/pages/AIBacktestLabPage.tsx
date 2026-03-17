import { Bot } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import {
  useBacktestParams,
  useLanguage,
  useSelectedCoin,
  useSelectedInterval,
} from '../store/useStore';
import {
  AI_BUILDER_INDICATOR_LIBRARY,
} from '../features/ai-lab/builderConfig';
import AIBacktestBuilderForm from '../features/ai-lab/components/AIBacktestBuilderForm';
import AIBacktestResultSection from '../features/ai-lab/components/AIBacktestResultSection';
import IndicatorCatalog from '../features/ai-lab/components/IndicatorCatalog';
import StrategyDraftPreview from '../features/ai-lab/components/StrategyDraftPreview';
import { useAIBacktestBuilder } from '../features/ai-lab/hooks/useAIBacktestBuilder';
import type { LlmProvider } from '../features/ai-lab/config';

interface AIBacktestLabPageProps {
  embedded?: boolean;
  runtimeConfig?: {
    provider: LlmProvider;
    apiKey?: string;
    model: string;
    temperature: number;
  };
}

export default function AIBacktestLabPage({
  embedded = false,
  runtimeConfig,
}: AIBacktestLabPageProps) {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const backtestParams = useBacktestParams();
  const isKo = language === 'ko';
  const [searchParams, setSearchParams] = useSearchParams();
  const isIndicatorListOnly = searchParams.get('view') === 'indicators';
  const {
    prompt,
    setPrompt,
    promptSamples,
    direction,
    setDirection,
    runInterval,
    setRunInterval,
    selectedIndicators,
    selectedStrategyId,
    setSelectedStrategyId,
    tp,
    setTp,
    sl,
    setSl,
    leverage,
    setLeverage,
    maxBars,
    setMaxBars,
    draft,
    copied,
    result,
    runError,
    draftAnswer,
    aiDraftPending,
    inferredStrategyId,
    strategies,
    intervals,
    backtestMutation,
    generateDraft,
    runDraftBacktest,
    copyDraft,
    strategyDisplayName,
  } = useAIBacktestBuilder({
    isKo,
    selectedCoin,
    selectedInterval,
    backtestParams,
    runtimeConfig,
  });

  const setIndicatorListMode = (enabled: boolean) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', 'builder');
    if (enabled) next.set('view', 'indicators');
    else next.delete('view');
    setSearchParams(next);
  };

  if (isIndicatorListOnly) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bot className="w-7 h-7 text-cyan-400" />
            {isKo ? 'AI 활용 가능 인디케이터 목록' : 'AI Available Indicator List'}
          </h1>
          <p className="text-dark-400 text-sm">
            {isKo
              ? '아래 목록은 현재 AI 백테스트 빌더에서 활용 가능한 인디케이터입니다.'
              : 'The list below contains indicators currently available in the AI backtest builder.'}
          </p>
          <div>
            <button
              onClick={() => setIndicatorListMode(false)}
              className="inline-flex text-xs px-3 py-1.5 rounded-lg border border-dark-600 bg-dark-800 text-dark-200 hover:bg-dark-700 transition-colors"
            >
              {isKo ? '빌더 화면으로 돌아가기' : 'Back to Builder'}
            </button>
          </div>
        </div>
        <IndicatorCatalog
          indicators={AI_BUILDER_INDICATOR_LIBRARY}
          selectedIndicatorIds={selectedIndicators}
          showSelectionState={false}
          isKo={isKo}
        />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${embedded ? '' : 'animate-fade-in'}`}>
      {!embedded && (
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bot className="w-7 h-7 text-cyan-400" />
            {isKo ? 'AI 백테스트 랩 (프론트엔드)' : 'AI Backtest Lab (Frontend)'}
          </h1>
          <p className="text-dark-400 text-sm">
            {isKo
              ? '전략 설명을 입력하면 실제 실행과 1:1로 일치하는 BacktestParams JSON을 생성합니다.'
              : 'Describe a strategy and generate BacktestParams JSON that matches execution 1:1.'}
          </p>
          <div className="text-xs text-dark-500">
            {isKo
              ? '실행 방식: 자연어 규칙 전체를 직접 코드화하지 않고, 현재 백테스트 엔진의 템플릿 전략으로 매핑해 실행'
              : 'Execution mode: map natural language to current template strategies, then run /backtest'}
          </div>
          <div>
            <button
              onClick={() => setIndicatorListMode(true)}
              className="inline-flex mt-1 text-xs px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-200 hover:bg-cyan-500/20 transition-colors"
            >
              {isKo ? '활용 가능한 인디케이터 목록만 보기' : 'View Only Available Indicator List'}
            </button>
          </div>
        </div>
      )}

      {embedded && (
        <div className="flex justify-end">
          <button
            onClick={() => setIndicatorListMode(true)}
            className="inline-flex text-xs px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-200 hover:bg-cyan-500/20 transition-colors"
          >
            {isKo ? '활용 가능한 인디케이터 목록만 보기' : 'View Only Available Indicator List'}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <div className="xl:col-span-3 space-y-4">
          <AIBacktestBuilderForm
            isKo={isKo}
            prompt={prompt}
            promptSamples={promptSamples}
            selectedStrategyId={selectedStrategyId}
            inferredStrategyId={inferredStrategyId}
            runInterval={runInterval}
            intervals={intervals}
            direction={direction}
            tp={tp}
            sl={sl}
            leverage={leverage}
            maxBars={maxBars}
            strategies={strategies}
            runError={runError}
            isGenerating={aiDraftPending}
            isRunning={backtestMutation.isPending}
            onPromptChange={setPrompt}
            onPromptSampleSelect={setPrompt}
            onStrategyChange={setSelectedStrategyId}
            onRunIntervalChange={setRunInterval}
            onDirectionChange={setDirection}
            onTpChange={setTp}
            onSlChange={setSl}
            onLeverageChange={setLeverage}
            onMaxBarsChange={setMaxBars}
            onGenerateDraft={generateDraft}
            onRunBacktest={runDraftBacktest}
          />
          {draftAnswer ? (
            <div className="card p-4 text-sm text-dark-200 border border-cyan-500/20 bg-cyan-500/5">
              <div className="text-xs uppercase tracking-wide text-cyan-300 mb-2">
                {isKo ? 'LLM 해석 결과' : 'LLM Interpretation'}
              </div>
              <div className="whitespace-pre-wrap">{draftAnswer}</div>
            </div>
          ) : null}
        </div>

        <div className="xl:col-span-2 space-y-4">
          <IndicatorCatalog
            indicators={AI_BUILDER_INDICATOR_LIBRARY}
            selectedIndicatorIds={selectedIndicators}
            showSelectionState={false}
            isKo={isKo}
          />

          <StrategyDraftPreview draft={draft} copied={copied} isKo={isKo} onCopy={copyDraft} />
        </div>
      </div>

      <AIBacktestResultSection
        isKo={isKo}
        result={result}
        strategyDisplayName={strategyDisplayName}
        selectedStrategyId={selectedStrategyId}
        direction={direction}
        runInterval={runInterval}
      />
    </div>
  );
}
