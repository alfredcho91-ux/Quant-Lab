import { useMemo } from 'react';
import type { EChartsCoreOption } from 'echarts/core';
import { TrendingUp } from 'lucide-react';
import EChart from '../../../components/EChart';
import type { ChartMode } from '../types';

interface GrowthChartProps {
  isKo: boolean;
  trades: number;
  compoundBalances: number[];
  simpleBalances: number[];
  chartMode: ChartMode;
  setChartMode: (mode: ChartMode) => void;
}

export function GrowthChart({
  isKo,
  trades,
  compoundBalances,
  simpleBalances,
  chartMode,
  setChartMode,
}: GrowthChartProps) {
  const option = useMemo<EChartsCoreOption>(() => {
    const categories = Array.from({ length: trades + 1 }, (_, index) => String(index));
    const series: Record<string, unknown>[] = [];
    if (chartMode === 'compound' || chartMode === 'both') {
      series.push({
        name: isKo ? '복리' : 'Compound',
        type: 'line',
        data: compoundBalances,
        showSymbol: false,
        smooth: false,
        lineStyle: { color: '#22c55e', width: 2.5 },
        areaStyle: chartMode === 'compound' ? { color: 'rgba(34, 197, 94, 0.18)' } : undefined,
      });
    }
    if (chartMode === 'simple' || chartMode === 'both') {
      series.push({
        name: isKo ? '단리' : 'Simple',
        type: 'line',
        data: simpleBalances,
        showSymbol: false,
        smooth: false,
        lineStyle: {
          color: '#f59e0b',
          width: 2.5,
          type: chartMode === 'both' ? 'dashed' : 'solid',
        },
        areaStyle: chartMode === 'simple' ? { color: 'rgba(245, 158, 11, 0.18)' } : undefined,
      });
    }

    return {
      animation: false,
      backgroundColor: 'rgba(18, 26, 43, 0.55)',
      color: ['#22c55e', '#f59e0b'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: '#334155',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        valueFormatter: (value: unknown) =>
          `₩${new Intl.NumberFormat('ko-KR').format(Number(value))}`,
      },
      legend: {
        show: chartMode === 'both',
        top: 4,
        left: 8,
        textStyle: { color: '#94a3b8', fontSize: 11 },
      },
      grid: { left: 72, right: 24, top: chartMode === 'both' ? 38 : 18, bottom: 48 },
      xAxis: {
        type: 'category',
        data: categories,
        name: isKo ? '트레이드 횟수' : 'Trades',
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { color: '#94a3b8', fontSize: 12 },
        axisLabel: { color: '#94a3b8', fontSize: 11 },
        axisLine: { lineStyle: { color: '#27324a' } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#94a3b8',
          fontSize: 11,
          formatter: (value: number) =>
            `₩${Intl.NumberFormat('ko-KR', { notation: 'compact' }).format(value)}`,
        },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.12)' } },
      },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series,
    } as EChartsCoreOption;
  }, [chartMode, compoundBalances, isKo, simpleBalances, trades]);

  const modes: { mode: ChartMode; label: string }[] = [
    { mode: 'compound', label: isKo ? '복리' : 'Compound' },
    { mode: 'simple', label: isKo ? '단리' : 'Simple' },
    { mode: 'both', label: isKo ? '비교' : 'Compare' },
  ];

  return (
    <div className="card min-w-0 p-4 sm:p-5">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-dark-400">
          <TrendingUp className="h-4 w-4" />
          {isKo ? '자본 성장 곡선' : 'Equity Growth Curve'}
        </div>
        <div className="grid grid-cols-3 rounded-lg border border-dark-700 bg-dark-900/60 p-1">
          {modes.map(({ mode, label }) => (
            <button
              key={mode}
              onClick={() => setChartMode(mode)}
              className={`min-w-0 rounded-md px-2 py-1.5 text-sm font-medium transition-colors sm:px-3 ${
                chartMode === mode
                  ? 'bg-primary-500 text-white'
                  : 'text-dark-300 hover:bg-dark-800 hover:text-dark-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <EChart option={option} height={320} />
    </div>
  );
}
