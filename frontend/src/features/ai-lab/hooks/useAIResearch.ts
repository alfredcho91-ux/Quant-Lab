/**
 * AI Research Hook – 백엔드 /api/ai/research 호출 (자연어 → LLM → 백테스트)
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { runAIResearch, runAIAnalyst } from '../../../api/client';
import type { BacktestResult } from '../../../types';
import type { LlmProvider } from '../config';
import type {
  ConditionalProbabilityAnalysis,
  OptimizationCharacteristicsAnalysis,
} from '../../../api/ai_lab';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export type { LlmProvider } from '../config';

export interface AIConfig {
  provider: LlmProvider;
  apiKey?: string;
  model: string;
  temperature: number;
  selectedCoin?: string;
  selectedInterval?: string;
  mode?: 'research' | 'analyst';
}

export type AIProgressStage =
  | 'idle'
  | 'interpreting'
  | 'extracting'
  | 'loading_data'
  | 'analyzing'
  | 'backtesting'
  | 'done'
  | 'error';

export function useAIResearch(language: string, config: AIConfig) {
  const isKo = language === 'ko';
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: isKo
        ? '안녕하세요! AI 백테스트 랩입니다. 전략을 자연어로 입력하면 LLM이 파라미터를 추출하고 백테스트를 실행합니다.'
        : 'Hello! This is AI Backtest Lab. Enter a strategy in natural language and we\'ll extract parameters and run a backtest.',
      timestamp: Date.now(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentResult, setCurrentResult] = useState<BacktestResult | null>(null);
  const [currentAnalysisResult, setCurrentAnalysisResult] = useState<ConditionalProbabilityAnalysis | null>(null);
  const [currentOptimizationInsights, setCurrentOptimizationInsights] = useState<OptimizationCharacteristicsAnalysis | null>(null);
  const [clarifyingQuestions, setClarifyingQuestions] = useState<string[]>([]);
  const [progressStage, setProgressStage] = useState<AIProgressStage>('idle');
  const [lastExecutionPath, setLastExecutionPath] = useState<string | null>(null);
  const [lastCacheHit, setLastCacheHit] = useState<boolean | null>(null);

  const stopProgressTimer = useCallback(() => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      stopProgressTimer();
    };
  }, [stopProgressTimer]);

  useEffect(() => {
    const mode = config.mode || 'research';
    const welcomeMsg: Message = {
      id: 'welcome',
      role: 'assistant',
      content: mode === 'analyst'
        ? (isKo
            ? '안녕하세요! AI 데이터 분석가입니다. 현재 시장 상황에 대해 궁금한 점을 물어보세요.'
            : 'Hello! I am your AI Data Analyst. Ask me anything about the current market conditions.')
        : (isKo
            ? '안녕하세요! AI 백테스트 랩입니다. 전략을 자연어로 입력하면 LLM이 파라미터를 추출하고 백테스트를 실행합니다.'
            : 'Hello! This is AI Backtest Lab. Enter a strategy in natural language and we\'ll extract parameters and run a backtest.'),
      timestamp: Date.now(),
    };
    setMessages([welcomeMsg]);
    setCurrentResult(null);
    setCurrentAnalysisResult(null);
    setCurrentOptimizationInsights(null);
    setClarifyingQuestions([]);
    setLastExecutionPath(null);
    setLastCacheHit(null);
    setProgressStage('idle');
  }, [config.mode, isKo]);

  const sendMessage = useCallback(async (text: string) => {
    const normalizedApiKey = (config.apiKey ?? '')
      .trim()
      // 복붙 시 앞뒤 따옴표/꺽쇠가 섞여 들어오는 경우 방지
      .replace(/^[<>"'`]+|[<>"'`]+$/g, '');

    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setCurrentResult(null);
    setCurrentAnalysisResult(null);
    setCurrentOptimizationInsights(null);
    setClarifyingQuestions([]);
    setLastExecutionPath(null);
    setLastCacheHit(null);
    setProgressStage('interpreting');

    stopProgressTimer();
    const progressFlow: AIProgressStage[] = [
      'interpreting',
      'extracting',
      'loading_data',
      'analyzing',
      'backtesting',
    ];
    let progressIndex = 0;
    progressTimerRef.current = setInterval(() => {
      progressIndex = Math.min(progressIndex + 1, progressFlow.length - 1);
      setProgressStage(progressFlow[progressIndex]);
    }, 1200);

    try {
      const uiContext =
        config.selectedCoin && config.selectedInterval
          ? `[UI_CONTEXT]\ncoin=${config.selectedCoin}\ninterval=${config.selectedInterval}`
          : '';
      const contextualPrompt = uiContext ? `${trimmed}\n\n${uiContext}` : trimmed;
      const history = messages
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      if (config.mode === 'analyst') {
        if (!config.selectedCoin || !config.selectedInterval) {
          throw new Error('Coin and Interval must be selected for Analyst mode');
        }
        const response = await runAIAnalyst({
          prompt: trimmed,
          coin: config.selectedCoin,
          interval: config.selectedInterval,
          api_key: normalizedApiKey || undefined,
          provider: config.provider,
          model: config.model,
          temperature: config.temperature,
          history,
        });

        if (response.success) {
          const aiMsg: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: response.answer,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, aiMsg]);
          setLastExecutionPath(response.execution_path ?? null);
          setLastCacheHit(response.cache_hit ?? null);
          setProgressStage('done');
        } else {
          const errorMsg: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `Error: ${response.error}`,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, errorMsg]);
          setProgressStage('error');
        }
        return;
      }

      const response = await runAIResearch({
        prompt: contextualPrompt,
        api_key: normalizedApiKey || undefined,
        provider: config.provider,
        model: config.model,
        temperature: config.temperature,
        history,
      });

      // 3. Handle Response
      if (response.success) {
        const aiMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.answer,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, aiMsg]);
        setLastExecutionPath(response.execution_path ?? null);
        setLastCacheHit(response.cache_hit ?? null);
        if (response.needs_clarification && response.clarifying_questions?.length) {
          setClarifyingQuestions(response.clarifying_questions);
        }

        if (response.analysis_result?.analysis_type === 'conditional_probability') {
          setCurrentAnalysisResult(response.analysis_result);
          setProgressStage('analyzing');
        } else {
          if (response.analysis_result?.analysis_type === 'optimization_characteristics') {
            setCurrentOptimizationInsights(response.analysis_result);
          }
          if (response.backtest_result) {
            setCurrentResult(response.backtest_result);
            setProgressStage('backtesting');
          }
        }
        setProgressStage('done');
      } else {
        // Error handling
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${response.error}`,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, errorMsg]);
        setProgressStage('error');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Network Error: ${message}`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setProgressStage('error');
    } finally {
      stopProgressTimer();
      setIsTyping(false);
    }
  }, [config, isKo, messages, stopProgressTimer]);

  return {
    messages,
    isTyping,
    currentResult,
    currentAnalysisResult,
    currentOptimizationInsights,
    clarifyingQuestions,
    progressStage,
    lastExecutionPath,
    lastCacheHit,
    sendMessage,
  };
}
