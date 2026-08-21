import { BarChart3 } from 'lucide-react';
import type { VPVRData } from '../types';

interface VPVRTableProps {
  data?: VPVRData;
  isLoading: boolean;
  isKo: boolean;
}

function formatPrice(value: number): string {
  const digits = value >= 1_000 ? 0 : value >= 1 ? 2 : 4;
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat(undefined, {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

export function VPVRTable({ data, isLoading, isKo }: VPVRTableProps) {
  const title = isKo ? 'VPVR 매물대' : 'VPVR Volume Profile';

  return (
    <section className="card overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-dark-700 px-4 py-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-white">{title}</h2>
        </div>
        {data && (
          <span className="font-mono text-[11px] text-dark-400">
            {data.interval} · {data.candle_count}{isKo ? '봉' : ' candles'} · ${formatPrice(data.price_low)} - ${formatPrice(data.price_high)}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="px-4 py-8 text-center text-sm text-dark-400">{isKo ? 'VPVR 계산 중...' : 'Calculating VPVR...'}</div>
      ) : !data ? (
        <div className="px-4 py-8 text-center text-sm text-dark-500">{isKo ? 'VPVR 데이터를 불러오지 못했습니다.' : 'VPVR data is unavailable.'}</div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-px border-b border-dark-700 bg-dark-700 sm:grid-cols-2 xl:grid-cols-4">
            <div className="bg-dark-800 px-4 py-2.5">
              <div className="text-[10px] text-dark-500">POC</div>
              <div className="mt-0.5 font-mono text-xs text-amber-300">
                {formatPrice(data.poc_price_low)} - {formatPrice(data.poc_price_high)}
              </div>
            </div>
            <div className="bg-dark-800 px-4 py-2.5">
              <div className="text-[10px] text-dark-500">VA {Math.round(data.value_area_pct * 100)}%</div>
              <div className="mt-0.5 font-mono text-xs text-primary-300">
                {formatPrice(data.value_area_low)} - {formatPrice(data.value_area_high)}
              </div>
            </div>
            <div className="bg-dark-800 px-4 py-2.5">
              <div className="text-[10px] text-dark-500">{isKo ? '현재가' : 'Last'}</div>
              <div className="mt-0.5 font-mono text-xs text-white">{formatPrice(data.current_price)}</div>
            </div>
            <div className="bg-dark-800 px-4 py-2.5">
              <div className="text-[10px] text-dark-500">{isKo ? '기간 VWAP' : 'Period VWAP'}</div>
              <div className="mt-0.5 font-mono text-xs text-primary-300">
                {data.vwap != null ? formatPrice(data.vwap) : '—'}
              </div>
            </div>
          </div>

          <div className="max-h-[440px] overflow-auto">
            <table className="w-full min-w-[640px] text-xs">
              <thead className="sticky top-0 z-10 bg-dark-800 text-dark-400">
                <tr className="border-b border-dark-700">
                  <th className="px-4 py-2 text-left font-medium">{isKo ? '가격대' : 'Price range'}</th>
                  <th className="px-4 py-2 text-left font-medium">{isKo ? '거래대금' : 'Volume'}</th>
                  <th className="w-[34%] px-4 py-2 text-left font-medium">{isKo ? '비중' : 'Share'}</th>
                  <th className="px-4 py-2 text-right font-medium">Taker Δ</th>
                  <th className="px-4 py-2 text-right font-medium">{isKo ? '구분' : 'Level'}</th>
                </tr>
              </thead>
              <tbody>
                {data.bins.filter((row) => row.volume > 0).map((row) => {
                  const rowTone = row.is_poc
                    ? 'bg-amber-500/10'
                    : row.is_current
                      ? 'bg-primary-500/10'
                      : row.is_value_area
                        ? 'bg-dark-700/35'
                        : '';
                  return (
                    <tr key={`${row.price_low}-${row.price_high}`} className={`border-b border-dark-800 ${rowTone}`}>
                      <td className="whitespace-nowrap px-4 py-2.5 font-mono text-dark-100">
                        {formatPrice(row.price_low)} - {formatPrice(row.price_high)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-2.5 font-mono text-dark-200">${formatCurrency(row.volume)}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 min-w-20 flex-1 overflow-hidden rounded-full bg-dark-700">
                            <div
                              className={row.is_poc ? 'h-full bg-amber-400' : 'h-full bg-primary-500'}
                              style={{ width: `${row.volume_pct}%` }}
                            />
                          </div>
                          <span className="w-10 text-right font-mono text-dark-300">{row.volume_pct.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className={`whitespace-nowrap px-4 py-2.5 text-right font-mono ${row.delta >= 0 ? 'text-bull' : 'text-bear'}`}>
                        {row.delta >= 0 ? '+' : '-'}${formatCurrency(Math.abs(row.delta))}
                      </td>
                      <td className="whitespace-nowrap px-4 py-2.5 text-right">
                        <div className="flex justify-end gap-1">
                          {row.is_poc && <span className="rounded border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-300">POC</span>}
                          {row.is_value_area && <span className="rounded border border-primary-500/30 bg-primary-500/10 px-1.5 py-0.5 text-[10px] text-primary-300">VA</span>}
                          {row.is_current && <span className="rounded border border-dark-500 px-1.5 py-0.5 text-[10px] text-dark-200">{isKo ? '현재' : 'Now'}</span>}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
