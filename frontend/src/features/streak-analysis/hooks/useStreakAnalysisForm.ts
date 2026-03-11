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
    use_complex_pattern: false,
    complex_pattern: null,
    rsi_threshold: 60.0,
  });

  // 몸통 총합 필터 (Simple Mode만)
  const [minTotalBodyPct, setMinTotalBodyPct] = useState<number | null>(null);

  const mutation = useMutation({
    mutationFn: runStreakAnalysis,
  });
  const resetMutation = mutation.reset;

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
      const pattern = generatePattern(useComplexPattern, condition1, condition2);

      const requestParams: StreakAnalysisParams = {
        coin: safeSelectedCoin,
        interval: params.interval,
        n_streak: useComplexPattern ? params.n_streak : condition1.count,
        direction: useComplexPattern ? params.direction : condition1.direction,
        use_complex_pattern: useComplexPattern,
        complex_pattern: pattern,
        rsi_threshold: params.rsi_threshold || 60.0,
        min_total_body_pct: useComplexPattern ? null : minTotalBodyPct, // Simple Mode만 적용
      };

      // Complex Mode에서 2차 조건 검증
      if (useComplexPattern && !condition2) {
        alert(
          isKo
            ? '복합 패턴 분석은 2차 조건이 필요합니다'
            : 'Complex pattern analysis requires 2nd condition'
        );
        return;
      }

      console.log('🚀 Running analysis with params:', requestParams);
      console.log('📊 Mode:', useComplexPattern ? 'Complex' : 'Simple');
      console.log('📋 Pattern:', pattern);

      mutation.mutate(requestParams, {
        onError: (error: unknown) => {
          console.error('❌ Analysis failed:', error);
          const msg = getErrorMessage(error);
          alert(isKo ? `분석 실패: ${msg}` : `Analysis failed: ${msg}`);
        },
        onSuccess: (data) => {
          console.log('✅ Analysis success:', data);
        },
      });
    } catch (error: unknown) {
      console.error('❌ Error in handleRun:', error);
      const msg = getErrorMessage(error);
      alert(isKo ? `오류 발생: ${msg}` : `Error: ${msg}`);
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
    // API
    mutation,
    handleRun,
    // Utils
    isKo,
    safeSelectedCoin,
  };
}
