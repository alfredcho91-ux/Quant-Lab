import { useMemo } from 'react';
import type { OHLCV } from '../types';
import { computeWickDistribution } from '../utils/wickStatistics';
import { wickBinLabel } from '../utils/wickStatisticsPresentation';
import { formatNum } from '../utils/format';

export function WickDistribution({ data, isKo }: { data: readonly OHLCV[]; isKo: boolean }) {
  const distribution = useMemo(() => computeWickDistribution(data), [data]);
  return (
    <section aria-labelledby="wick-distribution-title" className="card min-w-0 p-4">
      <h2 id="wick-distribution-title" className="text-sm font-semibold text-white">
        {isKo ? '꼬리 길이 분포 · 0.1%p 간격' : 'Wick length distribution · 0.1 percentage-point bins'}
      </h2>
      <p className="mt-1 text-xs text-dark-300">
        {isKo ? `전체 ${distribution.total}봉 · 유효 ${distribution.valid}봉 · 제외 ${distribution.excluded}봉`
          : `${distribution.total} total · ${distribution.valid} valid · ${distribution.excluded} excluded`}
      </p>
      <p className="mt-1 text-xs text-dark-400">
        {isKo ? '현재 불러온 완료 봉 전체 대상(최대 200봉). 각 봉 종가 대비 꼬리 %. 이동 통계 기간·표시 단위와 별개입니다.'
          : 'All loaded completed candles (up to 200). Each wick is divided by its own close. Independent of the rolling period and display unit.'}
      </p>
      <p className="mt-1 text-xs text-dark-400">
        {isKo ? '하한 이상·상한 미만. 길이 0은 첫 구간에 포함합니다. 양쪽 모두 빈 구간은 생략합니다. 비정상 OHLC 또는 구간을 계산할 수 없는 값은 제외하며, 비중은 유효 봉 수 기준입니다.'
          : 'Lower bound inclusive, upper bound exclusive. Zero wicks belong to the first bin. Bins empty on both sides are omitted. Invalid OHLC or unrepresentable bins are excluded; shares use the valid-candle count.'}
      </p>
      {distribution.valid === 0 ? (
        <p role="status" className="mt-3 text-sm text-dark-400">{isKo ? '분포를 계산할 유효 완료 봉이 없습니다.' : 'No valid completed candles for this distribution.'}</p>
      ) : (
        <div className="mt-3 max-h-80 overflow-auto rounded border border-dark-700">
          <table aria-label={isKo ? '윗꼬리·아랫꼬리 0.1% 분포' : 'Upper and lower wick 0.1% distribution'} className="w-full text-left text-xs">
            <thead className="sticky top-0 z-10 bg-dark-800 text-dark-300">
              <tr>
                <th scope="col" className="px-3 py-2">{isKo ? '구간(이상–미만)' : 'Range [lower, upper)'}</th>
                <th scope="col" className="px-3 py-2 text-sky-300">{isKo ? '윗꼬리 개수 · 비중' : 'Upper wick count · share'}</th>
                <th scope="col" className="px-3 py-2 text-emerald-300">{isKo ? '아랫꼬리 개수 · 비중' : 'Lower wick count · share'}</th>
              </tr>
            </thead>
            <tbody>
              {distribution.bins.map(bin => (
                <tr key={bin.index} className="border-t border-dark-700/50">
                  <th scope="row" className="whitespace-nowrap px-3 py-2 font-mono font-normal text-dark-300">{wickBinLabel(bin.index)}</th>
                  {(['upper', 'lower'] as const).map(side => {
                    const count = side === 'upper' ? bin.upperCount : bin.lowerCount;
                    const percent = side === 'upper' ? bin.upperPercent : bin.lowerPercent;
                    return (
                      <td key={side} className="min-w-36 px-3 py-2">
                        <span className="font-mono text-dark-200">{count}{isKo ? '개' : ''} · {formatNum(percent)}%</span>
                        <div aria-hidden="true" className="mt-1 h-1.5 overflow-hidden rounded bg-dark-700">
                          <div className={`h-full ${side === 'upper' ? 'bg-sky-400' : 'bg-emerald-400'}`} style={{ width: `${percent}%` }} />
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
