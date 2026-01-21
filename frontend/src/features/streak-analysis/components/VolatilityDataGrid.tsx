/**
 * 변동성 데이터 그리드 컴포넌트
 * 타점 결정 데이터 (Dip/Rise, ATR, Z-Score)
 */
import { Target } from 'lucide-react';
import type { StreakAnalysisResult } from '../../../types';

interface VolatilityDataGridProps {
  result: StreakAnalysisResult;
  direction: 'green' | 'red';
  isKo: boolean;
}

export default function VolatilityDataGrid({ result, direction, isKo }: VolatilityDataGridProps) {
  if (!result.volatility_stats) {
    return null;
  }

  const stats = result.volatility_stats;

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Target className="w-5 h-5 text-yellow-400" />
        {isKo ? '📊 타점 결정 데이터 (변동성)' : '📊 Entry Point Data (Volatility)'}
      </h3>
      <p className="text-dark-400 text-sm mb-4">
        {isKo
          ? `${result.n_streak}연속 ${direction === 'green' ? '양봉' : '음봉'} 다음 봉의 장중 변동성 통계`
          : `Intraday volatility stats for candle after ${result.n_streak}-streak`}
      </p>

      {/* Trimmed 안내 */}
      {stats.is_trimmed && (
        <div className="bg-dark-800/50 rounded-lg px-3 py-2 mb-4 text-xs text-dark-400 flex items-center gap-2">
          <span>✂️</span>
          <span>
            {isKo
              ? '극단값(최고/최저 1개씩) 제외한 통계입니다'
              : 'Trimmed stats (excluded top/bottom outliers)'}
          </span>
          <span className="text-dark-500">
            ({stats.sample_count}
            {isKo ? '건 중' : ' samples'})
          </span>
        </div>
      )}

      {/* 기본 변동성 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border border-blue-500/20 rounded-xl p-4 text-center">
          <div className="text-dark-400 text-xs mb-1">{isKo ? '평균 하락폭 (Dip)' : 'Avg Dip'}</div>
          <div className="text-2xl font-bold text-blue-400">
            {stats.avg_dip !== null ? `${stats.avg_dip}%` : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">{isKo ? '매수 타점 기준' : 'Entry Target'}</div>
        </div>
        <div className="bg-gradient-to-br from-rose-500/10 to-red-500/5 border border-rose-500/20 rounded-xl p-4 text-center">
          <div className="text-dark-400 text-xs mb-1">
            {isKo ? '실질 최대 하락폭' : 'Practical Max Dip'}
          </div>
          <div className="text-2xl font-bold text-rose-400">
            {stats.practical_max_dip !== null ? `${stats.practical_max_dip}%` : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">
            {isKo ? '손절 기준' : 'Stop Loss'}
            {stats.extreme_max_dip && (
              <span className="text-dark-600 ml-1">
                ({isKo ? '극단' : 'extreme'}: {stats.extreme_max_dip}%)
              </span>
            )}
          </div>
        </div>
        <div className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border border-emerald-500/20 rounded-xl p-4 text-center">
          <div className="text-dark-400 text-xs mb-1">{isKo ? '평균 상승폭 (Rise)' : 'Avg Rise'}</div>
          <div className="text-2xl font-bold text-emerald-400">
            {stats.avg_rise !== null ? `${stats.avg_rise}%` : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">{isKo ? '익절 기준' : 'Take Profit'}</div>
        </div>
        <div className="bg-gradient-to-br from-purple-500/10 to-violet-500/5 border border-purple-500/20 rounded-xl p-4 text-center">
          <div className="text-dark-400 text-xs mb-1">
            {isKo ? '하락 표준편차' : 'Dip Std Dev'}
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {stats.std_dip !== null ? `${stats.std_dip}%` : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">{isKo ? '신뢰도 지표' : 'Reliability'}</div>
        </div>
      </div>

      {/* ATR & Z-Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl p-4 text-center">
          <div className="text-dark-400 text-xs mb-1">{isKo ? '평균 ATR (%)' : 'Avg ATR %'}</div>
          <div className="text-2xl font-bold text-amber-400">
            {stats.avg_atr_pct !== null ? `${stats.avg_atr_pct}%` : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">{isKo ? '일평균 변동폭' : 'Daily Range'}</div>
        </div>
        <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/5 border border-cyan-500/20 rounded-xl p-4 text-center">
          <div className="text-dark-400 text-xs mb-1">{isKo ? '최근 하락폭' : 'Current Dip'}</div>
          <div className="text-2xl font-bold text-cyan-400">
            {stats.current_dip !== null ? `${stats.current_dip}%` : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">{isKo ? '가장 최근 케이스' : 'Latest Case'}</div>
        </div>
        <div
          className={`rounded-xl p-4 text-center border ${
            stats.z_score_interpretation === 'extreme'
              ? 'bg-gradient-to-br from-rose-500/20 to-red-500/10 border-rose-500/40'
              : stats.z_score_interpretation === 'unusual'
                ? 'bg-gradient-to-br from-amber-500/20 to-yellow-500/10 border-amber-500/40'
                : 'bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20'
          }`}
        >
          <div className="text-dark-400 text-xs mb-1">
            {isKo ? 'Z-Score (변동성 이상치)' : 'Z-Score (Outlier)'}
          </div>
          <div
            className={`text-2xl font-bold ${
              stats.z_score_interpretation === 'extreme'
                ? 'text-rose-400'
                : stats.z_score_interpretation === 'unusual'
                  ? 'text-amber-400'
                  : 'text-emerald-400'
            }`}
          >
            {stats.z_score_dip !== null ? stats.z_score_dip : '-'}
          </div>
          <div className="text-dark-500 text-xs mt-1">
            {stats.z_score_interpretation === 'extreme'
              ? isKo
                ? '🔥 극단적 (|Z|≥2)'
                : '🔥 Extreme'
              : stats.z_score_interpretation === 'unusual'
                ? isKo
                  ? '⚠️ 이례적 (|Z|≥1)'
                  : '⚠️ Unusual'
                : isKo
                  ? '✅ 정상 범위'
                  : '✅ Normal'}
          </div>
        </div>
      </div>
    </div>
  );
}
