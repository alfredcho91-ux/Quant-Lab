import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Sparkles, MessageSquareText, SlidersHorizontal, PlugZap, KeyRound } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { useLanguage, useSelectedCoin, useSelectedInterval } from '../store/useStore';
import { getLabels } from '../store/labels';
import ChatInterface from '../features/ai-lab/components/ChatInterface';
import { useAIResearch } from '../features/ai-lab/hooks/useAIResearch';
import {
  AI_CHAT_CONFIG_KEY,
  DEFAULT_MODEL_BY_PROVIDER,
  isDefaultProviderModel,
  type LlmProvider,
  isSupportedLlmProvider,
  normalizePreferredModel,
} from '../features/ai-lab/config';
import Chart from '../components/LazyChart';
import MetricCard from '../components/MetricCard';
import TradesTable from '../components/TradesTable';
import AIBacktestLabPage from './AIBacktestLabPage';
import ProbabilityAnalysisPanel from '../features/ai-lab/components/ProbabilityAnalysisPanel';
import OptimizationInsightsPanel from '../features/ai-lab/components/OptimizationInsightsPanel';
import AIProgressIndicator from '../features/ai-lab/components/AIProgressIndicator';

type AiTab = 'chat' | 'builder';

interface PersistedAiConfig {
  provider?: LlmProvider;
  model?: string;
  temperature?: number;
}

function readPersistedAiConfig(): PersistedAiConfig {
  try {
    const raw = localStorage.getItem(AI_CHAT_CONFIG_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as PersistedAiConfig;
  } catch {
    return {};
  }
}

export default function AIStrategyLabPage() {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const labels = getLabels(language);
  const isKo = language === 'ko';
  const [searchParams, setSearchParams] = useSearchParams();
  const tab: AiTab = searchParams.get('tab') === 'builder' ? 'builder' : 'chat';
  const persistedConfig = useMemo(readPersistedAiConfig, []);
  const [aiProvider, setAiProvider] = useState<LlmProvider>(() =>
    isSupportedLlmProvider(persistedConfig.provider)
      ? persistedConfig.provider
      : 'gemini'
  );
  const [aiModel, setAiModel] = useState<string>(() => {
    const storedModel = typeof persistedConfig.model === 'string' ? persistedConfig.model : '';
    return normalizePreferredModel(storedModel);
  });
  const [aiApiKey, setAiApiKey] = useState<string>('');
  const [showLlmModal, setShowLlmModal] = useState<boolean>(false);
  const [draftProvider, setDraftProvider] = useState<LlmProvider>('gemini');
  const [draftModel, setDraftModel] = useState<string>('');
  const [draftApiKey, setDraftApiKey] = useState<string>('');
  const [draftTemperature, setDraftTemperature] = useState<number>(0.3);
  const [aiTemperature, setAiTemperature] = useState<number>(() =>
    typeof persistedConfig.temperature === 'number' && Number.isFinite(persistedConfig.temperature)
      ? persistedConfig.temperature
      : 0.3
  );
  const [connectedModelLabel, setConnectedModelLabel] = useState<string | null>(null);
  const [mode, setMode] = useState<'research' | 'analyst'>('research');

  useEffect(() => {
    const payload = {
      provider: aiProvider,
      model: aiModel,
      temperature: aiTemperature,
    };
    localStorage.setItem(AI_CHAT_CONFIG_KEY, JSON.stringify(payload));
  }, [aiProvider, aiModel, aiTemperature]);

  const runtimeConfig = useMemo(
    () => ({
      provider: aiProvider,
      apiKey: aiApiKey.trim(),
      model: aiModel.trim() || DEFAULT_MODEL_BY_PROVIDER[aiProvider],
      temperature: aiTemperature,
      selectedCoin,
      selectedInterval,
      mode,
    }),
    [aiProvider, aiApiKey, aiModel, aiTemperature, selectedCoin, selectedInterval, mode]
  );

  const {
    messages,
    isTyping,
    currentResult,
    currentAnalysisResult,
    currentOptimizationInsights,
    progressStage,
    lastExecutionPath,
    lastCacheHit,
    sendMessage,
  } = useAIResearch(language, runtimeConfig);

  useEffect(() => {
    if (lastExecutionPath && lastExecutionPath.startsWith('llm')) {
      const activeModel = aiModel.trim() || DEFAULT_MODEL_BY_PROVIDER[aiProvider];
      setConnectedModelLabel(`${aiProvider} / ${activeModel}`);
    }
  }, [lastExecutionPath, aiProvider, aiModel]);

  const setTab = (nextTab: AiTab) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', nextTab);
    if (nextTab !== 'builder') {
      next.delete('view');
    }
    setSearchParams(next);
  };

  const openLlmModal = () => {
    setDraftProvider(aiProvider);
    setDraftModel(aiModel);
    setDraftApiKey(aiApiKey);
    setDraftTemperature(aiTemperature);
    setShowLlmModal(true);
  };

  const closeLlmModal = () => {
    setShowLlmModal(false);
    setDraftApiKey('');
  };

  const applyLlmConfig = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAiProvider(draftProvider);
    setAiModel(draftModel.trim() || DEFAULT_MODEL_BY_PROVIDER[draftProvider]);
    setAiApiKey(draftApiKey.trim());
    setAiTemperature(Math.max(0, Math.min(1, draftTemperature)));
    setConnectedModelLabel(null);
    setShowLlmModal(false);
    setDraftApiKey('');
  };

  const clearApiKey = () => {
    setAiApiKey('');
    setDraftApiKey('');
    setConnectedModelLabel(null);
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
          <Sparkles className="w-6 h-6 text-cyan-400" />
          {isKo ? 'AI 백테스트 랩' : 'AI Backtest Lab'}
        </h1>
        <p className="text-dark-400 text-sm mt-1">
          {mode === 'analyst'
            ? (isKo
                ? '현재 시장 데이터와 지표를 기반으로 AI가 심층 분석을 제공합니다.'
                : 'AI provides in-depth analysis based on current market data and indicators.')
            : (isKo
                ? '자연어로 전략을 입력하면 LLM이 백테스트 파라미터를 추출하고 실행합니다. 전략 빌더 탭에서 수동 조합도 가능합니다.'
                : 'Enter a strategy in natural language to run an AI-powered backtest, or use the Strategy Builder tab for manual setup.')
          }
        </p>
        <div className="inline-flex mt-3 rounded-lg border border-dark-600 overflow-hidden">
          <button
            onClick={() => setTab('chat')}
            className={`px-3 py-2 text-xs md:text-sm flex items-center gap-1.5 ${
              tab === 'chat' ? 'bg-cyan-500/20 text-cyan-200' : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
            }`}
          >
            <MessageSquareText className="w-4 h-4" />
            {isKo ? '채팅 랩' : 'Chat Lab'}
          </button>
          <button
            onClick={() => setTab('builder')}
            className={`px-3 py-2 text-xs md:text-sm flex items-center gap-1.5 border-l border-dark-600 ${
              tab === 'builder'
                ? 'bg-cyan-500/20 text-cyan-200'
                : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            {isKo ? '전략 빌더' : 'Strategy Builder'}
          </button>
        </div>
      </div>

      {tab === 'builder' ? (
        <AIBacktestLabPage embedded runtimeConfig={runtimeConfig} />
      ) : (
        <div className="h-[calc(100vh-11rem)] flex flex-col md:flex-row gap-6">
          <div className="w-full md:w-[420px] flex-shrink-0 h-full flex flex-col gap-3">
            <div className="card p-3 space-y-2">
              <div className="text-xs text-dark-300 flex items-center gap-1.5">
                <PlugZap className="w-3.5 h-3.5 text-primary-400" />
                {isKo ? 'LLM 연결' : 'LLM Connection'}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={openLlmModal}
                  className="px-2.5 py-1.5 text-xs rounded-md border border-dark-600 bg-dark-800 hover:bg-dark-700 text-dark-200"
                >
                  {isKo ? 'LLM 설정' : 'LLM Settings'}
                </button>
                {aiApiKey ? (
                  <button
                    type="button"
                    onClick={clearApiKey}
                    className="px-2.5 py-1.5 text-xs rounded-md border border-dark-600 bg-dark-800 hover:bg-dark-700 text-dark-300"
                  >
                    {isKo ? '키 해제' : 'Clear Key'}
                  </button>
                ) : null}
                <div className="text-[10px] text-dark-400">
                  {aiApiKey
                    ? (isKo ? '사용자 키 사용' : 'Using custom key')
                    : (isKo ? '서버 키 사용' : 'Using server key')}
                </div>
              </div>

              <div className="text-[11px] text-dark-300">
                {connectedModelLabel
                  ? (isKo ? `연결된 모델: ${connectedModelLabel}` : `Connected model: ${connectedModelLabel}`)
                  : (isKo ? '연결 상태: 미확인 (첫 요청 후 표시)' : 'Connection: not verified (shown after first request)')}
              </div>

              <p className="text-[10px] text-dark-500">
                {isKo
                  ? '제공자/모델/온도/API 키는 팝업에서 설정 후 확인 시 적용됩니다. API 키는 로컬스토리지에 저장되지 않습니다.'
                  : 'Provider/model/temperature/API key are applied from popup on confirm. API key is not stored in localStorage.'}
              </p>
            </div>

            <div className="flex bg-dark-800 p-1 rounded-lg border border-dark-600">
              <button
                onClick={() => setMode('research')}
                className={`flex-1 py-1.5 text-xs rounded-md transition-colors ${
                  mode === 'research' ? 'bg-dark-600 text-white font-medium' : 'text-dark-400 hover:text-dark-300'
                }`}
              >
                {isKo ? '전략 연구' : 'Strategy Research'}
              </button>
              <button
                onClick={() => setMode('analyst')}
                className={`flex-1 py-1.5 text-xs rounded-md transition-colors ${
                  mode === 'analyst' ? 'bg-primary-500/20 text-primary-200 font-medium' : 'text-dark-400 hover:text-dark-300'
                }`}
              >
                {isKo ? '데이터 분석' : 'Data Analyst'}
              </button>
            </div>

            <div className="flex-1 min-h-0">
              <ChatInterface
                messages={messages}
                isTyping={isTyping}
                isKo={isKo}
                onSend={sendMessage}
              />
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2">
            <AIProgressIndicator
              stage={progressStage}
              isKo={isKo}
              executionPath={lastExecutionPath}
              cacheHit={lastCacheHit}
            />

            {currentAnalysisResult ? (
              <ProbabilityAnalysisPanel analysis={currentAnalysisResult} isKo={isKo} />
            ) : currentResult ? (
              <div className="space-y-6 animate-slide-up">
                {currentOptimizationInsights ? (
                  <OptimizationInsightsPanel analysis={currentOptimizationInsights} isKo={isKo} />
                ) : null}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard label={labels.trades} value={`${currentResult.summary.n_trades}`} />
                  <MetricCard
                    label={labels.winrate}
                    value={`${currentResult.summary.win_rate.toFixed(2)}%`}
                    trend={currentResult.summary.win_rate >= 50 ? 'up' : 'down'}
                  />
                  <MetricCard
                    label={labels.cumret}
                    value={`${currentResult.summary.total_pnl >= 0 ? '+' : ''}${currentResult.summary.total_pnl.toFixed(1)}%`}
                    trend={currentResult.summary.total_pnl >= 0 ? 'up' : 'down'}
                  />
                  <MetricCard
                    label={labels.liqcnt}
                    value={`${currentResult.summary.liq_count}`}
                    trend={currentResult.summary.liq_count > 0 ? 'down' : 'neutral'}
                  />
                </div>

                <Chart
                  data={currentResult.chart_data}
                  trades={currentResult.trades}
                  title={isKo ? 'AI 백테스트 결과' : 'AI Backtest Result'}
                  showBB
                  showMA
                  height={500}
                />

                <TradesTable
                  trades={currentResult.trades}
                  regimeStats={currentResult.summary.regime_stats}
                />
              </div>
            ) : (
              <div className="flex-1 min-h-[320px] flex flex-col items-center justify-center text-dark-500 gap-3 border-2 border-dashed border-dark-700 rounded-xl bg-dark-800/30">
                <Sparkles className="w-12 h-12 opacity-25" />
                <p className="text-sm">
                  {isKo
                    ? '왼쪽 채팅창에 전략을 자연어로 입력하면 AI가 파라미터를 추출하고 백테스트 결과가 표시됩니다.'
                    : 'Enter a strategy in natural language in the chat to see AI-extracted backtest results.'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
      {showLlmModal && (
        <div className="fixed inset-0 z-[80] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md card p-4 border border-dark-600">
            <div className="flex items-center gap-2 mb-3">
              <KeyRound className="w-4 h-4 text-primary-400" />
              <h3 className="text-sm font-semibold text-white">
                {isKo ? 'LLM 연결 설정' : 'LLM Connection Settings'}
              </h3>
            </div>
            <form onSubmit={applyLlmConfig} className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={draftProvider}
                  onChange={(e) => {
                    const nextProvider = e.target.value as LlmProvider;
                    setDraftProvider(nextProvider);
                    if (!draftModel.trim() || isDefaultProviderModel(draftModel)) {
                      setDraftModel(DEFAULT_MODEL_BY_PROVIDER[nextProvider]);
                    }
                  }}
                  className="bg-dark-800 border border-dark-600 text-sm rounded-md px-2 py-2"
                >
                  <option value="gemini">Gemini</option>
                </select>
                <input
                  value={draftModel}
                  onChange={(e) => setDraftModel(e.target.value)}
                  placeholder={isKo ? '모델명' : 'Model'}
                  className="bg-dark-800 border border-dark-600 text-sm px-2 py-2 rounded-md"
                />
              </div>
              <input
                type="password"
                value={draftApiKey}
                onChange={(e) => setDraftApiKey(e.target.value)}
                placeholder={isKo ? 'AIza... 형태 키 입력' : 'Enter API key'}
                className="w-full bg-dark-800 border border-dark-600 text-sm px-3 py-2 rounded-md"
                autoComplete="off"
                spellCheck={false}
                autoFocus
              />
              <div>
                <label className="text-[11px] text-dark-400 block mb-1">temperature</label>
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.1}
                  value={draftTemperature}
                  onChange={(e) => setDraftTemperature(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
                  className="w-24 bg-dark-800 border border-dark-600 text-sm px-2 py-2 rounded-md"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={closeLlmModal}
                  className="px-3 py-1.5 text-xs rounded-md border border-dark-600 bg-dark-800 hover:bg-dark-700 text-dark-300"
                >
                  {isKo ? '취소' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-xs rounded-md border border-primary-500/40 bg-primary-500/20 hover:bg-primary-500/30 text-primary-200"
                >
                  {isKo ? '확인' : 'Confirm'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
