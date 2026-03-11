// hooks/useAnalysisMutation.ts
/**
 * 분석 페이지에서 공통으로 사용하는 Mutation Hook
 * 일관된 에러 처리와 파라미터 동기화
 */

import { useMutation } from '@tanstack/react-query';
import {
  useBacktestParams,
  useSelectedCoin,
  useSelectedInterval,
} from '../store/useStore';

interface UseAnalysisMutationOptions<TParams, TResult> {
  mutationFn: (params: TParams) => Promise<TResult>;
  onSuccess?: (data: TResult) => void;
  onError?: (error: unknown) => void;
}

/**
 * 분석 API 호출을 위한 공통 Mutation Hook
 * 
 * @param options - mutation 함수와 성공/에러 콜백
 * @returns mutation 객체와 handleRun 함수
 */
export function useAnalysisMutation<TParams extends { coin?: string; use_csv?: boolean }, TResult>(
  options: UseAnalysisMutationOptions<TParams, TResult>
) {
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const backtestParams = useBacktestParams();
  const { mutationFn, onSuccess, onError } = options;

  const mutation = useMutation({
    mutationFn,
    onSuccess,
    onError: (error) => {
      console.error('❌ Mutation error:', error);
      if (onError) {
        onError(error);
      }
    },
  });

  /**
   * 분석 실행 함수
   * 자동으로 coin과 use_csv를 전역 설정으로 동기화
   */
  const handleRun = (params: TParams) => {
    const next = {
      ...params,
      coin: selectedCoin,
      use_csv: backtestParams.use_csv,
    } as Record<string, unknown>;
    if ('interval' in next) next.interval = next.interval ?? selectedInterval;
    mutation.mutate(next as TParams);
  };

  return {
    mutation,
    handleRun,
    isPending: mutation.isPending,
    data: mutation.data,
    error: mutation.error,
  };
}
