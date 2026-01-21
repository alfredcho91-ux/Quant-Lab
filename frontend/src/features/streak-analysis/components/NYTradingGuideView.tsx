/**
 * 뉴욕 시간대 가이드 뷰 컴포넌트
 * 시간대별 저점/고점 확률 및 Plotly 차트
 */
import Plot from 'react-plotly.js';
import type { StreakAnalysisResult } from '../../../types';

interface NYTradingGuideViewProps {
  result: StreakAnalysisResult;
  interval: string;
  isKo: boolean;
}

export default function NYTradingGuideView({
  result,
  interval,
  isKo,
}: NYTradingGuideViewProps) {
  if (!result.ny_trading_guide || result.complex_pattern_analysis) {
    return null;
  }

  const guide = result.ny_trading_guide;

  return (
    <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-4 mb-4">
      <div className="text-blue-400 font-semibold mb-3 flex items-center gap-2">
        🌍 {isKo ? '뉴욕 시간대 가이드' : 'NY Trading Guide'}
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm mb-4">
        <div>
          <span className="text-dark-400">{isKo ? '진입 윈도우' : 'Entry Window'}:</span>
          <span className="text-white ml-2">{guide.entry_window}</span>
        </div>
        <div>
          <span className="text-dark-400">{isKo ? '피크 윈도우' : 'Peak Window'}:</span>
          <span className="text-white ml-2">{guide.peak_window}</span>
        </div>
        {guide.low_window && (
          <>
            <div>
              <span className="text-dark-400">{isKo ? '저점 윈도우' : 'Low Window'}:</span>
              <span className="text-white ml-2">{guide.low_window}</span>
            </div>
            <div>
              <span className="text-dark-400">{isKo ? '평균 변동성' : 'Avg Volatility'}:</span>
              <span className="text-white ml-2">{guide.avg_volatility}</span>
            </div>
          </>
        )}
      </div>

      {/* 시간대별 저점/고점 확률 그래프 - 1d/3d만 */}
      {interval !== '1w' &&
        interval !== '1M' &&
        (guide.hourly_low_probability || guide.hourly_high_probability) && (
          <div className="mt-4">
            <div className="text-white font-semibold mb-3 text-sm flex items-center gap-2">
              📊 {isKo ? '시간대별 저점/고점 발생 확률' : 'Hourly Low/High Occurrence Probability'}
            </div>
            <div className="bg-dark-900 rounded-lg p-2">
              <Plot
                data={[
                  ...(guide.hourly_low_probability &&
                  Object.keys(guide.hourly_low_probability).length > 0
                    ? [
                        {
                          x: Object.keys(guide.hourly_low_probability),
                          y: Object.values(guide.hourly_low_probability),
                          type: 'bar' as const,
                          name: isKo ? '저점 확률' : 'Low Probability',
                          marker: {
                            color: Object.values(guide.hourly_low_probability).map(
                              (prob: any) =>
                                prob > 0 ? 'rgba(6, 182, 212, 0.8)' : 'rgba(55, 65, 81, 0.5)'
                            ),
                          },
                        } as any,
                      ]
                    : []),
                  ...(guide.hourly_high_probability &&
                  Object.keys(guide.hourly_high_probability).length > 0
                    ? [
                        {
                          x: Object.keys(guide.hourly_high_probability),
                          y: Object.values(guide.hourly_high_probability),
                          type: 'bar' as const,
                          name: isKo ? '고점 확률' : 'High Probability',
                          marker: {
                            color: Object.values(guide.hourly_high_probability).map(
                              (prob: any) =>
                                prob > 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(55, 65, 81, 0.5)'
                            ),
                          },
                        } as any,
                      ]
                    : []),
                ]}
                layout={{
                  paper_bgcolor: 'rgba(0, 0, 0, 0)',
                  plot_bgcolor: 'rgba(0, 0, 0, 0)',
                  font: { color: '#9CA3AF' },
                  barmode: 'group',
                  xaxis: {
                    title: { text: isKo ? '시간 (EST)' : 'Time (EST)' },
                    gridcolor: 'rgba(55, 65, 81, 0.3)',
                  },
                  yaxis: {
                    title: { text: isKo ? '확률 (%)' : 'Probability (%)' },
                    range: [0, 100],
                    gridcolor: 'rgba(55, 65, 81, 0.3)',
                  },
                  height: 350,
                  margin: { l: 50, r: 20, t: 40, b: 50 },
                  legend: {
                    x: 0.5,
                    xanchor: 'center',
                    y: 1.1,
                    orientation: 'h',
                    font: { color: '#9CA3AF' },
                  },
                } as any}
                config={{ displayModeBar: false }}
                style={{ width: '100%', height: 350 }}
              />
            </div>
          </div>
        )}

      {/* 요일별 저점/고점 확률 그래프 - 주봉(1w)만 */}
      {interval === '1w' &&
        guide.daily_low_probability &&
        guide.daily_high_probability && (
          <div className="mt-4">
            <div className="text-white font-semibold mb-3 text-sm flex items-center gap-2">
              📅 {isKo ? '요일별 저점/고점 발생 확률' : 'Daily Low/High Occurrence Probability'}
            </div>
            <div className="bg-dark-900 rounded-lg p-2">
              <Plot
                data={[
                  {
                    x: isKo
                      ? ['월', '화', '수', '목', '금', '토', '일']
                      : Object.keys(guide.daily_low_probability!),
                    y: Object.values(guide.daily_low_probability!),
                    type: 'bar' as const,
                    name: isKo ? '저점 확률' : 'Low Probability',
                    marker: {
                      color: (Object.values(guide.daily_low_probability!) as number[]).map(
                        (prob: number) => (prob > 20 ? 'rgba(6, 182, 212, 1)' : 'rgba(6, 182, 212, 0.6)')
                      ),
                    },
                  } as any,
                  {
                    x: isKo
                      ? ['월', '화', '수', '목', '금', '토', '일']
                      : Object.keys(guide.daily_high_probability!),
                    y: Object.values(guide.daily_high_probability!),
                    type: 'bar' as const,
                    name: isKo ? '고점 확률' : 'High Probability',
                    marker: {
                      color: (Object.values(guide.daily_high_probability!) as number[]).map(
                        (prob: number) =>
                          prob > 20 ? 'rgba(16, 185, 129, 1)' : 'rgba(16, 185, 129, 0.6)'
                      ),
                    },
                  } as any,
                ]}
                layout={{
                  paper_bgcolor: 'rgba(0, 0, 0, 0)',
                  plot_bgcolor: 'rgba(0, 0, 0, 0)',
                  font: { color: '#9CA3AF' },
                  barmode: 'group',
                  xaxis: {
                    title: { text: isKo ? '요일' : 'Day of Week' },
                    gridcolor: 'rgba(55, 65, 81, 0.3)',
                  },
                  yaxis: {
                    title: { text: isKo ? '확률 (%)' : 'Probability (%)' },
                    range: [0, 50],
                    gridcolor: 'rgba(55, 65, 81, 0.3)',
                  },
                  height: 350,
                  margin: { l: 50, r: 20, t: 40, b: 50 },
                  legend: {
                    x: 0.5,
                    xanchor: 'center',
                    y: 1.1,
                    orientation: 'h',
                    font: { color: '#9CA3AF' },
                  },
                } as any}
                config={{ displayModeBar: false }}
                style={{ width: '100%', height: 350 }}
              />
            </div>
            <p className="text-dark-400 text-xs mt-2">{guide.note}</p>
          </div>
        )}
    </div>
  );
}
