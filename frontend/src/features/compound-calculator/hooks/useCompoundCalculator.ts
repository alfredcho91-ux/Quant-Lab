import { useMemo, useState } from 'react';
import {
  buildCompoundGrowth,
  buildRiskRows,
  buildSimpleGrowth,
  buildTradeScenario,
  buildSummaryRows,
  calculateEvPerR,
  getNearest,
  HEATMAP_RR_VALUES,
  HEATMAP_WIN_RATES,
} from '../calculations';
import type { ChartMode } from '../types';

export function useCompoundCalculator(isKo: boolean) {
  const [capital, setCapital] = useState(10_000_000);
  const [trades, setTrades] = useState(100);
  const [risk, setRisk] = useState(2);
  const [rr, setRr] = useState(2);
  const [winRate, setWinRate] = useState(50);
  const [slippage, setSlippage] = useState(0.1);
  const [chartMode, setChartMode] = useState<ChartMode>('compound');
  const initialCapital = Math.max(capital, 0);
  const scenario = useMemo(() => buildTradeScenario(trades, winRate), [trades, winRate]);

  const compound = useMemo(
    () => buildCompoundGrowth(initialCapital, risk, rr, slippage, scenario),
    [initialCapital, risk, rr, scenario, slippage]
  );
  const simpleBalances = useMemo(
    () => buildSimpleGrowth(initialCapital, risk, rr, slippage, scenario),
    [initialCapital, risk, rr, scenario, slippage]
  );
  const evPerR = useMemo(() => calculateEvPerR(winRate, rr, slippage), [winRate, rr, slippage]);
  const finalCapital = compound.balances[compound.balances.length - 1] ?? initialCapital;
  const roi = initialCapital > 0 ? (finalCapital / initialCapital - 1) * 100 : 0;
  const summaryRows = useMemo(
    () => buildSummaryRows(initialCapital, trades, compound.balances, simpleBalances),
    [compound.balances, initialCapital, simpleBalances, trades]
  );
  const riskRows = useMemo(
    () => buildRiskRows(trades, winRate, risk, slippage, isKo),
    [isKo, risk, slippage, trades, winRate]
  );

  return {
    capital,
    setCapital,
    trades,
    setTrades,
    risk,
    setRisk,
    rr,
    setRr,
    winRate,
    setWinRate,
    slippage,
    setSlippage,
    chartMode,
    setChartMode,
    initialCapital,
    scenario,
    compound,
    simpleBalances,
    evPerR,
    finalCapital,
    roi,
    summaryRows,
    riskRows,
    nearestWinRate: getNearest(HEATMAP_WIN_RATES, winRate),
    nearestRr: getNearest(HEATMAP_RR_VALUES, rr),
  };
}
