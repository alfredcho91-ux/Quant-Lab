import { TrendIndicatorsLatest } from '../types';

export type TrendBias = 'bullish' | 'bearish' | 'neutral';

/** 현재 K vs D: K > D → 골든(상승), K < D → 데드(하락). 배경색에 사용 */
export function getStochState(k: number | null | undefined, d: number | null | undefined): 'golden' | 'dead' | null {
  if (k == null || d == null || Number.isNaN(k) || Number.isNaN(d)) return null;
  if (k > d) return 'golden';
  if (k < d) return 'dead';
  return null;
}

/** 시계열 마지막 값으로 K vs D 상태 (latest가 null일 때 배경색 fallback) */
export function getAlignedStochTail(
  tk: string[] | undefined,
  vk: number[] | undefined,
  td: string[] | undefined,
  vd: number[] | undefined,
  count: number
): Array<{ k: number; d: number }> {
  if (!tk?.length || !vk?.length || !td?.length || !vd?.length) return [];

  const dByTime = new Map<string, number>();
  const dLen = Math.min(td.length, vd.length);
  for (let i = 0; i < dLen; i++) {
    const d = vd[i];
    if (typeof d === 'number' && !Number.isNaN(d)) {
      dByTime.set(td[i], d);
    }
  }

  const out: Array<{ k: number; d: number }> = [];
  const kLen = Math.min(tk.length, vk.length);
  for (let i = kLen - 1; i >= 0; i--) {
    const k = vk[i];
    if (typeof k !== 'number' || Number.isNaN(k)) continue;
    const d = dByTime.get(tk[i]);
    if (typeof d !== 'number' || Number.isNaN(d)) continue;
    out.push({ k, d });
    if (out.length >= count) break;
  }

  return out.reverse();
}

export function getStochStateFromSeries(
  tk: string[] | undefined,
  vk: number[] | undefined,
  td: string[] | undefined,
  vd: number[] | undefined
): 'golden' | 'dead' | null {
  const tail = getAlignedStochTail(tk, vk, td, vd, 1);
  if (tail.length === 0) return null;
  return getStochState(tail[0].k, tail[0].d);
}

/** 직전 봉 대비 크로스 발생 시에만: 골든크로스 / 데드크로스 텍스트용 */
export function getStochCross(
  tk: string[] | undefined,
  vk: number[] | undefined,
  td: string[] | undefined,
  vd: number[] | undefined
): 'golden' | 'dead' | null {
  const tail = getAlignedStochTail(tk, vk, td, vd, 2);
  if (tail.length < 2) return null;

  const prev = tail[0];
  const cur = tail[1];
  if (prev.k <= prev.d && cur.k > cur.d) return 'golden';
  if (prev.k >= prev.d && cur.k < cur.d) return 'dead';
  return null;
}

export function getTrendBiasBadgeClass(bias: TrendBias): string {
  if (bias === 'bullish') return 'bg-primary-500/15 text-primary-300 border-primary-500/30';
  if (bias === 'bearish') return 'bg-red-500/15 text-red-300 border-red-500/30';
  return 'bg-dark-700/50 text-dark-200 border-dark-600';
}

export function getTrendBiasLabel(bias: TrendBias, isKo: boolean): string {
  if (bias === 'bullish') return isKo ? '상승 우위' : 'Bullish Bias';
  if (bias === 'bearish') return isKo ? '하락 우위' : 'Bearish Bias';
  return isKo ? '중립' : 'Neutral';
}

export function calculateTrendBias(
  latest: TrendIndicatorsLatest,
  stochState: 'golden' | 'dead' | null
): TrendBias {
  let score = 0;
  let votes = 0;
  const pushVote = (vote: boolean | null) => {
    if (vote == null) return;
    votes += 1;
    score += vote ? 1 : -1;
  };

  pushVote(latest.rsi != null ? latest.rsi >= 50 : null);
  pushVote(latest.macd_hist != null ? latest.macd_hist >= 0 : null);
  pushVote(latest.supertrend_dir != null ? latest.supertrend_dir > 0 : null);
  pushVote(latest.close != null && latest.sma20 != null ? latest.close >= latest.sma20 : null);
  pushVote(latest.close != null && latest.vwap_20 != null ? latest.close >= latest.vwap_20 : null);
  pushVote(stochState != null ? stochState === 'golden' : null);

  if (votes === 0) return 'neutral';
  if (score >= 2) return 'bullish';
  if (score <= -2) return 'bearish';
  return 'neutral';
}
