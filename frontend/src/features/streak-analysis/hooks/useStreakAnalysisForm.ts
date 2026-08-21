/**
 * Streak Analysis 폼 상태 및 API 요청 관리 Hook
 */
import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { runStreakAnalysis } from '../../../api/client';
import { useSelectedCoin, useSelectedInterval } from '../../../store/useStore';
import { usePageCommon } from '../../../hooks/usePageCommon';
import type { StreakAnalysisParams } from '../../../types';
import { generatePattern, type PatternCondition } from '../utils/patternHelper';
import { getErrorMessage } from '../../../utils/error';

export function useStreakAnalysisForm() {
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const { isKo } = usePageCommon();
  const safeSelectedCoin = selectedCoin || 'BTC';

  // 복합 패턴 분석 체크박스 로직
  const [useComplexPattern, setUseComplexPattern] = useState(false);
  const [condition1, setCondition1] = useState<PatternCondition>({
    count: 3,
    direction: 'green',
  });
  const [condition2, setCondition2] = useState<PatternCondition>({
    count: 2,
    direction: 'red',
  });

  const [params, setParams] = useState<StreakAnalysisParams>({
    coin: safeSelectedCoin,
    interval: selectedInterval,
    n_streak: 3,
    direction: 'green',
    candle_mode: 'standard',
    use_complex_pattern: false,
    complex_pattern: null,
    rsi_threshold: 60.0,
    ema_200_position: null,
  });

  // 몸통 총합 필터 (Simple Mode만)
  const [minTotalBodyPct, setMinTotalBodyPct] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: runStreakAnalysis,
  });
  const resetMutation = mutation.reset;

  const handleCandleModeChange = (candleMode: NonNullable<StreakAnalysisParams['candle_mode']>) => {
    setParams((prev) => ({ ...prev, candle_mode: candleMode }));
    resetMutation();
  };

  // 코인·타임프레임(사이드바) 변경 시 동기화
  useEffect(() => {
    setParams((p) => ({
      ...p,
      ...(selectedCoin ? { coin: selectedCoin } : {}),
      interval: selectedInterval,
    }));
    // 사이드바 변경 시 이전 분석 결과를 초기화해 stale 결과 오해를 방지
    resetMutation();
  }, [selectedCoin, selectedInterval, resetMutation]);

  // 패턴 자동 생성 (조건 변경 시)
  useEffect(() => {
    const pattern = generatePattern(useComplexPattern, condition1, condition2);
    setParams((p) => ({
      ...p,
      use_complex_pattern: useComplexPattern,
      complex_pattern: pattern,
      // Simple Mode일 때 n_streak과 direction 업데이트
      n_streak: useComplexPattern ? p.n_streak : condition1.count,
      direction: useComplexPattern ? p.direction : condition1.direction,
    }));
  }, [useComplexPattern, condition1, condition2, selectedCoin]);

  // API 호출
  const handleRun = () => {
    try {
      setFormError(null);
      const pattern = generatePattern(useComplexPattern, condition1, condition2);

      const requestParams: StreakAnalysisParams = {
        coin: safeSelectedCoin,
        interval: params.interval,
        n_streak: useComplexPattern ? params.n_streak : condition1.count,
        direction: useComplexPattern ? params.direction : condition1.direction,
        candle_mode: params.candle_mode ?? 'standard',
        use_complex_pattern: useComplexPattern,
        complex_pattern: pattern,
        rsi_threshold: params.rsi_threshold || 60.0,
        min_total_body_pct: useComplexPattern ? null : minTotalBodyPct, // Simple Mode만 적용
        ema_200_position: params.ema_200_position ?? null,
      };

      // Complex Mode에서 2차 조건 검증
      if (useComplexPattern && !condition2) {
        setFormError(
          isKo
            ? '복합 패턴 분석은 2차 조건이 필요합니다'
            : 'Complex pattern analysis requires 2nd condition'
        );
        return;
      }

      mutation.mutate(requestParams);
    } catch (error: unknown) {
      const msg = getErrorMessage(error);
      setFormError(isKo ? `오류 발생: ${msg}` : `Error: ${msg}`);
    }
  };

  return {
    // State
    useComplexPattern,
    setUseComplexPattern,
    condition1,
    setCondition1,
    condition2,
    setCondition2,
    minTotalBodyPct,
    setMinTotalBodyPct,
    params,
    setParams,
    handleCandleModeChange,
    // API
    mutation,
    handleRun,
    formError,
    // Utils
    isKo,
    safeSelectedCoin,
  };
}
