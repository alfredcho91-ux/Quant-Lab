import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { getStrategies, getTimeframes, runBacktest } from '../../../api/client';
import type { BacktestParams, BacktestResult, Strategy } from '../../../types';
import { runAIResearch } from '../../../api/ai_lab';
import { DEFAULT_MODEL_BY_PROVIDER, type LlmProvider } from '../config';
import {
  AI_BUILDER_INDICATOR_LIBRARY,
  AI_BUILDER_PROMPT_SAMPLES_EN,
  AI_BUILDER_PROMPT_SAMPLES_KO,
} from '../builderConfig';
import type { Direction } from '../types';

interface UseAIBacktestBuilderOptions {
  isKo: boolean;
  selectedCoin: string;
  selectedInterval: string;
  backtestParams: BacktestParams;
  runtimeConfig?: {
    provider: LlmProvider;
    apiKey?: string;
    model: string;
    temperature: number;
  };
}

const DEFAULT_INTERVALS = ['1h', '4h', '1d'];

export function useAIBacktestBuilder({
  isKo,
  selectedCoin,
  selectedInterval,
  backtestParams,
  runtimeConfig,
}: UseAIBacktestBuilderOptions) {
  const promptSamples = useMemo(
    () => (isKo ? AI_BUILDER_PROMPT_SAMPLES_KO : AI_BUILDER_PROMPT_SAMPLES_EN),
    [isKo]
  );

  const [prompt, setPrompt] = useState<string>(() =>
    isKo ? AI_BUILDER_PROMPT_SAMPLES_KO[0] : AI_BUILDER_PROMPT_SAMPLES_EN[0]
  );
  const [direction, setDirection] = useState<Direction>('Long');
  const [runInterval, setRunInterval] = useState<string>(selectedInterval);
  const selectedIndicators = useMemo(
    () => AI_BUILDER_INDICATOR_LIBRARY.map((item) => item.id),
    []
  );
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>('Connors');
  const [inferredStrategyId, setInferredStrategyId] = useState<string>('');
  const [tp, setTp] = useState<number>(2.0);
  const [sl, setSl] = useState<number>(1.0);
  const [leverage, setLeverage] = useState<number>(1);
  const [maxBars, setMaxBars] = useState<number>(48);
  const [draft, setDraft] = useState<BacktestParams | null>(null);
  const [copied, setCopied] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [aiDraftPending, setAiDraftPending] = useState(false);
  const [draftAnswer, setDraftAnswer] = useState<string | null>(null);

  const { data: strategiesData } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
    staleTime: Infinity,
  });

  const strategies = strategiesData ?? [];

  const { data: tfData } = useQuery({
    queryKey: ['timeframes', selectedCoin],
    queryFn: () => getTimeframes(selectedCoin),
  });

  const intervals = tfData?.all ?? DEFAULT_INTERVALS;

  useEffect(() => {
    setRunInterval(selectedInterval);
  }, [selectedInterval]);

  useEffect(() => {
    const allSamples = [...AI_BUILDER_PROMPT_SAMPLES_KO, ...AI_BUILDER_PROMPT_SAMPLES_EN];
    if (allSamples.includes(prompt) && prompt !== promptSamples[0]) {
      setPrompt(promptSamples[0]);
    }
  }, [prompt, promptSamples]);

  useEffect(() => {
    if (strategies.length === 0) return;
    if (!strategies.some((strategy: Strategy) => strategy.id === selectedStrategyId)) {
      setSelectedStrategyId(strategies[0].id);
    }
  }, [selectedStrategyId, strategies]);

  const backtestMutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: (data) => {
      if (data) {
        setResult(data);
        setRunError(null);
        return;
      }
      setRunError(
        isKo
          ? '백테스트 실행에 실패했습니다. 전략/파라미터를 조정해 다시 시도하세요.'
          : 'Backtest failed. Adjust strategy/params and retry.'
      );
    },
    onError: () => {
      setRunError(
        isKo
          ? '백테스트 요청 중 오류가 발생했습니다.'
          : 'Backtest request failed.'
      );
    },
  });

  const parseNumber = (value: unknown, fallback: number): number => {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string') {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) return parsed;
    }
    return fallback;
  };

  const parseIntSafe = (value: unknown, fallback: number): number => {
    const parsed = parseNumber(value, fallback);
    return Math.max(1, Math.round(parsed));
  };

  const buildExecutableParams = (
    strategyId: string,
    nextDirection: BacktestParams['direction'],
    nextRunInterval: string,
    nextTp: number,
    nextSl: number,
    nextMaxBars: number,
    nextLeverage: number
  ): BacktestParams => {
    return {
      ...backtestParams,
      coin: selectedCoin,
      interval: nextRunInterval,
      strategy_id: strategyId,
      direction: nextDirection,
      leverage: Math.max(1, Math.min(125, Math.round(nextLeverage) || 1)),
      tp_pct: nextTp,
      sl_pct: nextSl,
      max_bars: nextMaxBars,
      use_csv: true,
    };
  };

  const generateDraft = async () => {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      setRunError(isKo ? '프롬프트를 먼저 입력하세요.' : 'Enter a prompt first.');
      return;
    }

    setAiDraftPending(true);
    setRunError(null);
    setDraftAnswer(null);
    setInferredStrategyId('');

    const provider = runtimeConfig?.provider ?? 'gemini';
    const model =
      runtimeConfig?.model?.trim() || DEFAULT_MODEL_BY_PROVIDER[provider];
    const temperature = Math.max(
      0,
      Math.min(1, Number(runtimeConfig?.temperature ?? 0.3))
    );
    const apiKey = (runtimeConfig?.apiKey ?? '').trim() || undefined;

    const builderContext = [
      '[BUILDER_CONTEXT]',
      `preferred_strategy=${selectedStrategyId}`,
      `preferred_direction=${direction}`,
      `preferred_interval=${runInterval}`,
      `selected_indicators=${selectedIndicators.join(',') || 'none'}`,
      `tp_pct=${tp}`,
      `sl_pct=${sl}`,
      `max_bars=${maxBars}`,
      '',
      '[UI_CONTEXT]',
      `coin=${selectedCoin}`,
      `interval=${runInterval}`,
    ].join('\n');

    try {
      const response = await runAIResearch({
        prompt: `${trimmedPrompt}\n\n${builderContext}`,
        api_key: apiKey,
        provider,
        model,
        temperature,
        history: [],
      });

      if (!response.success) {
        setRunError(
          response.error ||
            (isKo ? 'AI 요청 중 오류가 발생했습니다.' : 'AI request failed.')
        );
        return;
      }

      setDraftAnswer(response.answer || null);

      const params = response.backtest_params as Record<string, unknown> | undefined;
      if (!params) {
        setRunError(
          response.answer ||
            (isKo
              ? 'AI가 실행 가능한 전략 파라미터를 반환하지 않았습니다.'
              : 'AI did not return executable strategy params.')
        );
        return;
      }

      const nextStrategy = String(params.strategy_id || selectedStrategyId);
      const nextDirectionRaw = String(params.direction || direction);
      const nextDirection: Direction =
        nextDirectionRaw === 'Short'
          ? 'Short'
          : nextDirectionRaw === 'Both'
            ? 'Both'
            : 'Long';
      const nextInterval =
        typeof params.interval === 'string' && params.interval.trim()
          ? params.interval.trim()
          : runInterval;
      const nextTp = parseNumber(params.tp_pct, tp);
      const nextSl = parseNumber(params.sl_pct, sl);
      const nextMaxBars = parseIntSafe(params.max_bars, maxBars);
      const nextLeverage = Math.max(
        1,
        Math.min(125, parseIntSafe(params.leverage, leverage))
      );

      setSelectedStrategyId(nextStrategy);
      setInferredStrategyId(nextStrategy);
      setDirection(nextDirection);
      setRunInterval(nextInterval);
      setTp(nextTp);
      setSl(nextSl);
      setMaxBars(nextMaxBars);
      setLeverage(nextLeverage);

      const executableDirection: BacktestParams['direction'] =
        nextDirection === 'Short' ? 'Short' : 'Long';
      const executableParams = buildExecutableParams(
        nextStrategy,
        executableDirection,
        nextInterval,
        nextTp,
        nextSl,
        nextMaxBars,
        nextLeverage
      );
      setDraft(executableParams);

      if (response.backtest_result) {
        setResult(response.backtest_result);
      }
    } finally {
      setAiDraftPending(false);
    }
  };

  const runDraftBacktest = () => {
    if (direction === 'Both') {
      setRunError(
        isKo
          ? '실행은 Long 또는 Short 하나를 선택해야 합니다.'
          : 'Pick Long or Short for execution.'
      );
      return;
    }

    setRunError(null);

    const params =
      draft ??
      buildExecutableParams(
        selectedStrategyId,
        direction,
        runInterval,
        tp,
        sl,
        maxBars,
        leverage
      );
    setDraft(params);

    backtestMutation.mutate(params);
  };

  const copyDraft = async () => {
    if (!draft) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(draft, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setRunError(isKo ? '클립보드 복사에 실패했습니다.' : 'Clipboard copy failed.');
    }
  };

  const selectedStrategy = strategies.find((strategy) => strategy.id === selectedStrategyId);
  const strategyDisplayName = selectedStrategy
    ? isKo
      ? selectedStrategy.name_ko
      : selectedStrategy.name_en
    : selectedStrategyId;

  return {
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
  };
}
