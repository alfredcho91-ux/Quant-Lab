/**
 * 분석 컨트롤 패널 컴포넌트
 * 타임프레임 선택, 패턴 설정, 실행 버튼
 */
import { RefreshCw, BarChart2 } from 'lucide-react';
import type { PatternCondition } from '../utils/patternHelper';
import { getPatternPreview } from '../utils/patternHelper';

const TIMEFRAMES = [
  { label: '월봉', value: '1M' },
  { label: '주봉', value: '1w' },
  { label: '1일봉', value: '1d' },
  { label: '3일봉', value: '3d' },
  { label: '4시간봉', value: '4h' },
  { label: '2시간봉', value: '2h' },
  { label: '1시간봉', value: '1h' },
];

const TIMEFRAMES_EN = [
  { label: 'Monthly', value: '1M' },
  { label: 'Weekly', value: '1w' },
  { label: '1 Day', value: '1d' },
  { label: '3 Days', value: '3d' },
  { label: '4 Hours', value: '4h' },
  { label: '2 Hours', value: '2h' },
  { label: '1 Hour', value: '1h' },
];

interface AnalysisControlsProps {
  // State
  interval: string;
  useComplexPattern: boolean;
  condition1: PatternCondition;
  condition2: PatternCondition;
  minTotalBodyPct: number | null;
  isPending: boolean;
  isKo: boolean;
  // Handlers
  onIntervalChange: (interval: string) => void;
  onUseComplexPatternChange: (value: boolean) => void;
  onCondition1Change: (condition: PatternCondition) => void;
  onCondition2Change: (condition: PatternCondition) => void;
  onMinTotalBodyPctChange: (value: number | null) => void;
  onRun: () => void;
}

export default function AnalysisControls({
  interval,
  useComplexPattern,
  condition1,
  condition2,
  minTotalBodyPct,
  isPending,
  isKo,
  onIntervalChange,
  onUseComplexPatternChange,
  onCondition1Change,
  onCondition2Change,
  onMinTotalBodyPctChange,
  onRun,
}: AnalysisControlsProps) {
  const timeframes = isKo ? TIMEFRAMES : TIMEFRAMES_EN;

  return (
    <div className="card p-6 space-y-5">
      {/* 타임프레임 선택 */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-2">
          {isKo ? '⏱️ 타임프레임' : '⏱️ Timeframe'}
        </label>
        <select
          value={interval}
          onChange={(e) => onIntervalChange(e.target.value)}
          className="w-full bg-dark-800 border border-dark-600 rounded-xl px-4 py-3 text-white focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all"
        >
          {timeframes.map((tf) => (
            <option key={tf.value} value={tf.value}>
              {tf.label}
            </option>
          ))}
        </select>
      </div>

      {/* 패턴 분석 설정 */}
      <div className="border-t border-dark-700 pt-5 space-y-5">
        {/* 복합 패턴 분석 체크박스 */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="use_complex_pattern"
            checked={useComplexPattern}
            onChange={(e) => onUseComplexPatternChange(e.target.checked)}
            className="w-5 h-5 rounded border-dark-600 bg-dark-800 text-cyan-500 focus:ring-cyan-500"
          />
          <label
            htmlFor="use_complex_pattern"
            className="text-sm font-semibold text-cyan-400 cursor-pointer"
          >
            {isKo ? '🔍 복합 패턴 분석' : '🔍 Complex Pattern Analysis'}
          </label>
        </div>

        {/* 1차 조건 */}
        <div className="bg-dark-800/50 rounded-lg p-4 border border-dark-700">
          <h4 className="text-sm font-semibold text-cyan-400 mb-3">
            {isKo
              ? `1차 조건 ${!useComplexPattern ? '(메인 분석)' : ''}`
              : `1st Condition ${!useComplexPattern ? '(Main Analysis)' : ''}`}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-dark-400 mb-2">
                {isKo ? '연속 개수' : 'Consecutive Count'}
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={condition1.count}
                onChange={(e) => {
                  const newCount = Math.max(1, parseInt(e.target.value) || 1);
                  onCondition1Change({ ...condition1, count: newCount });
                }}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs text-dark-400 mb-2">
                {isKo ? '방향' : 'Direction'}
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => onCondition1Change({ ...condition1, direction: 'green' })}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    condition1.direction === 'green'
                      ? 'bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/50'
                      : 'bg-dark-700 text-dark-300 border-2 border-transparent hover:bg-dark-600'
                  }`}
                >
                  {isKo ? '양봉' : 'Green'}
                </button>
                <button
                  type="button"
                  onClick={() => onCondition1Change({ ...condition1, direction: 'red' })}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    condition1.direction === 'red'
                      ? 'bg-rose-500/20 text-rose-400 border-2 border-rose-500/50'
                      : 'bg-dark-700 text-dark-300 border-2 border-transparent hover:bg-dark-600'
                  }`}
                >
                  {isKo ? '음봉' : 'Red'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 2차 조건 - 복합 패턴 활성화 시에만 표시 */}
        {useComplexPattern && (
          <div className="bg-dark-800/50 rounded-lg p-4 border border-purple-500/50">
            <h4 className="text-sm font-semibold text-purple-400 mb-3 flex items-center gap-2">
              {isKo ? '2차 조건 (조정 구간)' : '2nd Condition (Adjustment Period)'}
              <span className="text-xs text-rose-400 font-normal">
                {isKo ? '*필수' : '*Required'}
              </span>
            </h4>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-dark-400 mb-2">
                    {isKo ? '연속 개수' : 'Consecutive Count'}
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={condition2.count}
                    onChange={(e) => {
                      const newCount = Math.max(1, parseInt(e.target.value) || 1);
                      onCondition2Change({ ...condition2, count: newCount });
                    }}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-dark-400 mb-2">
                    {isKo ? '방향' : 'Direction'}
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => onCondition2Change({ ...condition2, direction: 'green' })}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                        condition2.direction === 'green'
                          ? 'bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/50'
                          : 'bg-dark-700 text-dark-300 border-2 border-transparent hover:bg-dark-600'
                      }`}
                    >
                      {isKo ? '양봉' : 'Green'}
                    </button>
                    <button
                      type="button"
                      onClick={() => onCondition2Change({ ...condition2, direction: 'red' })}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                        condition2.direction === 'red'
                          ? 'bg-rose-500/20 text-rose-400 border-2 border-rose-500/50'
                          : 'bg-dark-700 text-dark-300 border-2 border-transparent hover:bg-dark-600'
                      }`}
                    >
                      {isKo ? '음봉' : 'Red'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 패턴 미리보기 */}
        <div className="bg-dark-800/30 rounded-lg p-3 border border-dark-700">
          <strong className="text-sm text-dark-300">
            {isKo ? '생성될 패턴:' : 'Generated Pattern:'}
          </strong>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span className="text-white font-mono">
              {getPatternPreview(useComplexPattern, condition1, condition2, isKo)}
            </span>
          </div>
        </div>

        {/* 몸통 총합 필터 (Simple Mode만) */}
        {!useComplexPattern && (
          <div className="bg-dark-800/50 rounded-lg p-4 border border-dark-700">
            <h4 className="text-sm font-semibold text-amber-400 mb-3">
              {isKo ? '📊 몸통 총합 필터 (선택)' : '📊 Total Body Filter (Optional)'}
            </h4>
            <div className="space-y-2">
              <label className="block text-xs text-dark-400 mb-2">
                {isKo
                  ? `${condition1.count}개 연속 봉의 몸통 총합 최소값 (%)`
                  : `Minimum total body % for ${condition1.count} consecutive candles`}
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={minTotalBodyPct ?? ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    onMinTotalBodyPctChange(value === '' ? null : parseFloat(value) || null);
                  }}
                  placeholder={isKo ? '예: 10.0' : 'e.g., 10.0'}
                  className="flex-1 bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:border-amber-500"
                />
                <button
                  type="button"
                  onClick={() => onMinTotalBodyPctChange(null)}
                  className="px-3 py-2 bg-dark-700 hover:bg-dark-600 text-dark-300 text-xs rounded-lg border border-dark-600 transition-colors"
                >
                  {isKo ? '초기화' : 'Clear'}
                </button>
              </div>
              <p className="text-xs text-dark-500 mt-2">
                {isKo
                  ? '• 비워두면 필터 미적용 (모든 패턴 분석)'
                  : '• Leave empty to disable filter (analyze all patterns)'}
                <br />
                {isKo
                  ? `• 예: 10.0 입력 시 ${condition1.count}개 봉의 몸통 총합이 10% 이상인 경우만 분석`
                  : `• e.g., 10.0 means only patterns with total body sum ≥ 10%`}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 실행 버튼 */}
      <button
        onClick={onRun}
        disabled={isPending}
        className="w-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 
          text-white font-bold py-4 px-6 rounded-xl transition-all transform hover:scale-[1.01] 
          disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
          flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20"
      >
        {isPending ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            {isKo ? '분석 중...' : 'Analyzing...'}
          </>
        ) : (
          <>
            <BarChart2 className="w-5 h-5" />
            {isKo ? '🚀 연속성 분석 실행' : '🚀 Run Streak Analysis'}
          </>
        )}
      </button>
    </div>
  );
}
