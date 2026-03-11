/**
 * 통계 요약 컨테이너
 * 세부 렌더링은 모드별 컴포넌트로 분리
 */
import type { StreakAnalysisResult } from '../../../types';
import ComplexModeSummary from './ComplexModeSummary';
import SimpleModeSummary from './SimpleModeSummary';

interface StatisticsSummaryProps {
  result: StreakAnalysisResult;
  direction: 'green' | 'red';
  isKo: boolean;
}

export default function StatisticsSummary({ result, direction, isKo }: StatisticsSummaryProps) {
  return (
    <div className="space-y-6">
      <SimpleModeSummary result={result} direction={direction} isKo={isKo} />
      <ComplexModeSummary result={result} isKo={isKo} />
    </div>
  );
}
