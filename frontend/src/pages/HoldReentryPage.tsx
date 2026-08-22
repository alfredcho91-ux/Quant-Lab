import { useMemo, useState } from 'react';
import { GitCompareArrows, RotateCcw, TrendingDown, TrendingUp } from 'lucide-react';
import { useLanguage } from '../store/useStore';
import {
  BASE_FEE_PERCENT,
  calculateHoldReentry,
  MAX_LEVERAGE,
  type TradeDirection,
  type HoldReentryInputs,
} from '../utils/holdReentry';

const DEFAULT_INPUTS: HoldReentryInputs = {
  direction: 'long',
  entryPrice: 64_000,
  currentPrice: 63_600,
  reentryPrice: 63_000,
  targetPrice: 65_000,
  marginUsd: 64_000,
  leverage: 1,
  feePercent: BASE_FEE_PERCENT,
};

type PriceField = 'entryPrice' | 'currentPrice' | 'reentryPrice' | 'targetPrice' | 'marginUsd' | 'leverage' | 'feePercent';

function formatAmount(value: number): string {
  const absolute = Math.abs(value);
  const digits = absolute >= 1_000 ? 0 : absolute >= 1 ? 2 : 4;
  return absolute.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function formatPnl(value: number): string {
  return `${value >= 0 ? '+' : '-'}$${formatAmount(value)}`;
}

function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function pnlColor(value: number): string {
  if (value > 0) return 'text-bull';
  if (value < 0) return 'text-bear';
  return 'text-dark-300';
}

interface MetricRowProps {
  label: string;
  value: string;
  valueClassName?: string;
}

function MetricRow({ label, value, valueClassName = 'text-white' }: MetricRowProps) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2 text-sm">
      <span className="text-dark-400">{label}</span>
      <span className={`shrink-0 font-mono font-semibold ${valueClassName}`}>{value}</span>
    </div>
  );
}

export default function HoldReentryPage() {
  const isKo = useLanguage() === 'ko';
  const [inputs, setInputs] = useState<HoldReentryInputs>(DEFAULT_INPUTS);
  const result = useMemo(() => calculateHoldReentry(inputs), [inputs]);
  const verdictIsPositive = result.netReentryAdvantage > 0;
  const verdictIsNeutral = result.netReentryAdvantage === 0;
  const verdict = verdictIsNeutral
    ? isKo
      ? '손익 동일'
      : 'Equivalent outcome'
    : verdictIsPositive
      ? isKo
        ? '재진입 성공 시 → 재진입 유리'
        : 'If re-entry succeeds → re-entry is favorable'
      : isKo
        ? '재진입 성공 시에도 → 홀딩 유리'
        : 'Even if re-entry succeeds → holding is favorable';

  const updateNumber = (field: PriceField, value: number) => {
    setInputs((previous) => ({ ...previous, [field]: Number.isFinite(value) ? value : 0 }));
  };

  const updateDirection = (direction: TradeDirection) => {
    setInputs((previous) => ({ ...previous, direction }));
  };

  const inputFields: Array<{ field: PriceField; label: string; step: number; max?: number }> = [
    { field: 'entryPrice', label: isKo ? '기존 진입' : 'Initial entry', step: 1 },
    { field: 'currentPrice', label: isKo ? '현재가' : 'Current price', step: 1 },
    { field: 'reentryPrice', label: isKo ? '예상 재진입' : 'Expected re-entry', step: 1 },
    { field: 'targetPrice', label: isKo ? '목표가' : 'Target price', step: 1 },
    { field: 'marginUsd', label: isKo ? '투입금 (USDT)' : 'Margin (USDT)', step: 1 },
    { field: 'leverage', label: isKo ? '레버리지 (배)' : 'Leverage (x)', step: 1, max: MAX_LEVERAGE },
    { field: 'feePercent', label: isKo ? '편도 수수료 (%)' : 'One-way fee (%)', step: 0.01, max: 10 },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header className="border-b border-dark-700 pb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
          <GitCompareArrows className="h-6 w-6 text-primary-400" />
          {isKo ? '홀딩 vs 재진입' : 'Hold vs Re-entry'}
        </h1>
      </header>

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(280px,360px)_minmax(0,1fr)]">
        <section className="rounded-lg border border-dark-700 bg-dark-800/30 p-4 sm:p-5">
          <div className="flex items-center justify-between gap-3 border-b border-dark-700 pb-3">
            <h2 className="text-sm font-semibold text-white">{isKo ? '가격 및 비용' : 'Prices and costs'}</h2>
            <button
              type="button"
              onClick={() => setInputs(DEFAULT_INPUTS)}
              className="rounded p-1.5 text-dark-400 hover:bg-dark-700 hover:text-white"
              title={isKo ? '예시 값으로 초기화' : 'Reset to example values'}
              aria-label={isKo ? '예시 값으로 초기화' : 'Reset to example values'}
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {inputFields.map(({ field, label, step, max }) => (
              <label key={field} className="min-w-0">
                <span className="mb-1.5 block text-xs text-dark-400">{label}</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min={field === 'leverage' ? 1 : 0}
                  max={max}
                  step={step}
                  value={inputs[field]}
                  onChange={(event) => updateNumber(field, event.target.valueAsNumber)}
                  className="w-full rounded-md border border-dark-600 bg-dark-900 px-3 py-2 font-mono text-sm text-white outline-none transition-colors focus:border-primary-400"
                />
              </label>
            ))}
          </div>
          <div className="mt-4">
            <span className="mb-1.5 block text-xs text-dark-400">{isKo ? '포지션 방향' : 'Position direction'}</span>
            <div className="grid grid-cols-2 gap-2" role="group" aria-label={isKo ? '포지션 방향' : 'Position direction'}>
              <button
                type="button"
                onClick={() => updateDirection('long')}
                className={`flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold transition-colors ${
                  inputs.direction === 'long'
                    ? 'border-bull bg-bull/15 text-bull'
                    : 'border-dark-600 bg-dark-900 text-dark-400 hover:border-dark-500 hover:text-dark-200'
                }`}
              >
                <TrendingUp className="h-4 w-4" />
                {isKo ? '롱' : 'Long'}
              </button>
              <button
                type="button"
                onClick={() => updateDirection('short')}
                className={`flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold transition-colors ${
                  inputs.direction === 'short'
                    ? 'border-bear bg-bear/15 text-bear'
                    : 'border-dark-600 bg-dark-900 text-dark-400 hover:border-dark-500 hover:text-dark-200'
                }`}
              >
                <TrendingDown className="h-4 w-4" />
                {isKo ? '숏' : 'Short'}
              </button>
            </div>
          </div>
          {result.isValid && (
            <div className="mt-4 grid grid-cols-2 border-y border-dark-700 text-xs sm:grid-cols-4 sm:divide-x sm:divide-dark-700">
              <div className="py-2 pr-2">
                <div className="text-dark-500">{isKo ? '포지션 규모' : 'Position size'}</div>
                <div className="mt-0.5 font-mono font-medium text-dark-100">${formatAmount(result.positionNotional)}</div>
              </div>
              <div className="px-2 py-2">
                <div className="text-dark-500">{isKo ? '기존 수량' : 'Initial size'}</div>
                <div className="mt-0.5 font-mono font-medium text-dark-100">{result.positionQuantity.toFixed(4)}</div>
              </div>
              <div className="border-t border-dark-700 py-2 pr-2 sm:border-t-0 sm:px-2">
                <div className="text-dark-500">{isKo ? '재진입 수량' : 'Re-entry size'}</div>
                <div className="mt-0.5 font-mono font-medium text-dark-100">{result.reentryQuantity.toFixed(4)}</div>
              </div>
              <div className="border-t border-dark-700 px-2 py-2 sm:border-t-0 sm:pl-2 sm:pr-0">
                <div className="text-dark-500">{isKo ? '적용 편도 수수료' : 'Applied one-way fee'}</div>
                <div className="mt-0.5 font-mono font-medium text-dark-100">{result.effectiveFeePercent.toFixed(2)}%</div>
              </div>
            </div>
          )}
          <div className="mt-2 text-[11px] text-dark-500">
            {isKo
              ? '입력한 편도 수수료가 각 청산·재진입 체결 비용에 적용됩니다.'
              : 'The entered one-way fee is applied to each exit and re-entry fill.'}
          </div>
        </section>

        <section className="rounded-lg border border-dark-700 bg-dark-800/30 p-4 sm:p-5">
          {!result.isValid ? (
            <div className="py-12 text-center text-sm text-dark-400">
              {isKo ? `가격·투입금은 0보다 커야 하고 레버리지는 1~${MAX_LEVERAGE}배, 수수료는 0~10%여야 합니다.` : `Prices and margin must be positive; leverage must be 1-${MAX_LEVERAGE}x and the fee must be 0-10%.`}
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 border-b border-dark-700 pb-3">
                <h2 className="text-sm font-semibold text-white">{isKo ? '비교 결과' : 'Comparison'}</h2>
                <span className="font-mono text-sm text-dark-300">
                  {isKo ? '현재 손익' : 'Current P&L'}{' '}
                  <span className={pnlColor(result.currentPnl)}>{formatPercent(result.currentPnlPercent)}</span>
                </span>
              </div>

              <div className="mt-4 grid gap-5 md:grid-cols-2">
                <div className="border-b border-dark-700 pb-4 md:border-b-0 md:border-r md:pr-5">
                  <h3 className="text-sm font-semibold text-white">{isKo ? '홀딩' : 'Hold'}</h3>
                  <div className="mt-2 divide-y divide-dark-700/80">
                    <MetricRow
                      label={isKo ? '목표 도달 시' : 'At target'}
                      value={formatPercent(result.holdingPnlPercent)}
                      valueClassName={pnlColor(result.holdingPnl)}
                    />
                    <MetricRow
                      label={isKo ? '손익' : 'P&L'}
                      value={formatPnl(result.holdingPnl)}
                      valueClassName={pnlColor(result.holdingPnl)}
                    />
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-white">
                    {isKo ? '손절 → 재진입' : 'Exit → Re-entry'}
                  </h3>
                  <div className="mt-2 divide-y divide-dark-700/80">
                    <MetricRow
                      label={isKo ? '확정 손익' : 'Realized P&L'}
                      value={formatPnl(result.realizedPnl)}
                      valueClassName={pnlColor(result.realizedPnl)}
                    />
                    <MetricRow
                      label={isKo ? '재진입 후 수익' : 'P&L after re-entry'}
                      value={formatPnl(result.reentryPnl)}
                      valueClassName={pnlColor(result.reentryPnl)}
                    />
                    <MetricRow
                      label={isKo ? '최종 손익' : 'Final P&L'}
                      value={formatPnl(result.reentryFinalPnl)}
                      valueClassName={pnlColor(result.reentryFinalPnl)}
                    />
                  </div>
                </div>
              </div>

              <div className="mt-5 grid divide-y divide-dark-700 border-y border-dark-700 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                <div className="py-3 sm:pr-4">
                  <div className="text-xs text-dark-400">{isKo ? '재진입 추가이득' : 'Gross re-entry gain'}</div>
                  <div className={`mt-1 font-mono text-lg font-bold ${pnlColor(result.grossReentryAdvantage)}`}>
                    {formatPnl(result.grossReentryAdvantage)}
                  </div>
                </div>
                <div className="py-3 sm:px-4">
                  <div className="text-xs text-dark-400">{isKo ? '추가 거래비용' : 'Additional fees'}</div>
                  <div className="mt-1 font-mono text-lg font-bold text-bear">-{formatPnl(result.incrementalFees).slice(1)}</div>
                </div>
                <div className="py-3 sm:pl-4">
                  <div className="text-xs text-dark-400">{isKo ? '순 추가이득' : 'Net re-entry gain'}</div>
                  <div className={`mt-1 font-mono text-lg font-bold ${pnlColor(result.netReentryAdvantage)}`}>
                    {formatPnl(result.netReentryAdvantage)}
                  </div>
                </div>
              </div>

              <div
                className={`mt-5 border-l-2 py-1 pl-3 text-sm font-semibold ${
                  verdictIsNeutral
                    ? 'border-dark-500 text-dark-200'
                    : verdictIsPositive
                      ? 'border-bull text-bull'
                      : 'border-bear text-bear'
                }`}
              >
                <span className="mr-3 text-xs font-medium text-dark-400">{isKo ? '판정' : 'Verdict'}</span>
                {verdict}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
