// hooks/usePageCommon.ts
/** 
 * 모든 페이지에서 공통으로 사용하는 훅
 * 반복되는 패턴을 추출하여 코드 중복 제거
 */

import {
  useBacktestParams,
  useLanguage,
  useSelectedCoin,
  useSelectedInterval,
} from '../store/useStore';
import { getLabels } from '../store/labels';
import { useQuery } from '@tanstack/react-query';
import { getTimeframes } from '../api/client';

export function usePageCommon() {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const backtestParams = useBacktestParams();
  const labels = getLabels(language);
  const isKo = language === 'ko';

  // Timeframes query (여러 페이지에서 사용)
  const { data: tfData } = useQuery({
    queryKey: ['timeframes', selectedCoin],
    queryFn: () => getTimeframes(selectedCoin),
  });

  const timeframes = tfData?.all || ['1h', '4h', '1d'];
  const availableTfs = tfData?.binance || ['15m', '1h', '4h', '1d'];

  return {
    language,
    selectedCoin,
    selectedInterval,
    backtestParams,
    labels,
    isKo,
    tfData,
    timeframes,
    availableTfs,
  };
}
