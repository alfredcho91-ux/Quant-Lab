import { useMemo } from 'react';
import type { EChartsCoreOption } from 'echarts/core';
import EChart from './EChart';
import type { OHLCV, Trade, SRLevel } from '../types';

export interface ChartProps {
  data: OHLCV[];
  trades?: Trade[];
  srLevels?: SRLevel[];
  title?: string;
  showBB?: boolean;
  showMA?: boolean;
  height?: number;
}

function lineSeries(name: string, values: Array<number | null>, color: string, dashed = false) {
  return {
    name,
    type: 'line',
    data: values,
    showSymbol: false,
    connectNulls: false,
    lineStyle: { color, width: 1, type: dashed ? 'dashed' : 'solid' },
    emphasis: { disabled: true },
    xAxisIndex: 0,
    yAxisIndex: 0,
  };
}

export default function Chart({
  data,
  trades = [],
  srLevels = [],
  title = 'Price Chart',
  showBB = true,
  showMA = true,
  height = 600,
}: ChartProps) {
  const option = useMemo<EChartsCoreOption>(() => {
    const categories = data.map((row) => row.open_dt);
    const supportResistanceLines = srLevels.map((level) => ({
      name: level.label || `${level.kind} ${level.price}`,
      yAxis: level.price,
      lineStyle: {
        color:
          level.kind === 'support'
            ? '#4caf50'
            : level.kind === 'resistance'
              ? '#ef5350'
              : '#ffb300',
        type: 'dashed',
        width: 1,
      },
      label: { show: false },
    }));

    const series: Record<string, unknown>[] = [
      {
        name: 'Price',
        type: 'candlestick',
        data: data.map((row) => [row.open, row.close, row.low, row.high]),
        itemStyle: {
          color: '#26a69a',
          color0: '#ef5350',
          borderColor: '#26a69a',
          borderColor0: '#ef5350',
        },
        markLine: {
          symbol: ['none', 'none'],
          silent: true,
          data: supportResistanceLines,
        },
        xAxisIndex: 0,
        yAxisIndex: 0,
      },
    ];

    if (showMA && data[0]?.SMA_main !== undefined) {
      series.push(lineSeries('SMA 200', data.map((row) => row.SMA_main ?? null), '#fbbf24'));
    }
    if (showMA && data[0]?.SMA_1 !== undefined) {
      series.push(lineSeries('MA 20', data.map((row) => row.SMA_1 ?? null), '#00bcd4'));
    }
    if (showMA && data[0]?.SMA_2 !== undefined) {
      series.push(lineSeries('MA 60', data.map((row) => row.SMA_2 ?? null), '#ff9800'));
    }
    if (showBB && data[0]?.BB_Up !== undefined) {
      series.push(
        lineSeries('BB Upper', data.map((row) => row.BB_Up ?? null), '#64748b', true),
        lineSeries('BB Lower', data.map((row) => row.BB_Low ?? null), '#64748b', true)
      );
    }
    if (data[0]?.RSI !== undefined) {
      series.push({
        name: 'RSI(14)',
        type: 'line',
        data: data.map((row) => row.RSI ?? null),
        showSymbol: false,
        lineStyle: { color: '#9fa8da', width: 1 },
        markLine: {
          symbol: ['none', 'none'],
          silent: true,
          label: { show: false },
          data: [
            { yAxis: 70, lineStyle: { color: '#ef5350', type: 'dashed' } },
            { yAxis: 30, lineStyle: { color: '#26a69a', type: 'dashed' } },
          ],
        },
        xAxisIndex: 1,
        yAxisIndex: 1,
      });
    }

    const markerGroups = [
      {
        name: 'Long Entry',
        rows: trades.filter((trade) => trade.Direction === 'Long'),
        timeKey: 'Entry Time' as const,
        priceKey: 'Entry Price' as const,
        color: '#00bcd4',
        symbol: 'triangle',
        rotate: 0,
      },
      {
        name: 'Short Entry',
        rows: trades.filter((trade) => trade.Direction === 'Short'),
        timeKey: 'Entry Time' as const,
        priceKey: 'Entry Price' as const,
        color: '#e040fb',
        symbol: 'triangle',
        rotate: 180,
      },
      {
        name: 'Win',
        rows: trades.filter((trade) => trade.PnL > 0),
        timeKey: 'Exit Time' as const,
        priceKey: 'Exit Price' as const,
        color: '#00e676',
        symbol: 'diamond',
        rotate: 0,
      },
      {
        name: 'Loss',
        rows: trades.filter((trade) => trade.PnL <= 0),
        timeKey: 'Exit Time' as const,
        priceKey: 'Exit Price' as const,
        color: '#ff1744',
        symbol: 'pin',
        rotate: 0,
      },
    ];

    markerGroups.forEach((group) => {
      if (group.rows.length === 0) return;
      series.push({
        name: group.name,
        type: 'scatter',
        data: group.rows.map((trade) => [trade[group.timeKey], trade[group.priceKey]]),
        symbol: group.symbol,
        symbolRotate: group.rotate,
        symbolSize: 10,
        itemStyle: { color: group.color },
        xAxisIndex: 0,
        yAxisIndex: 0,
      });
    });

    return {
      animation: false,
      backgroundColor: 'rgba(30, 41, 59, 0.5)',
      title: {
        text: title,
        left: 14,
        top: 10,
        textStyle: { color: '#f1f5f9', fontSize: 16, fontWeight: 600 },
      },
      legend: {
        top: 38,
        left: 12,
        textStyle: { color: '#94a3b8', fontSize: 10 },
        itemWidth: 14,
        itemHeight: 8,
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: '#334155',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
      },
      grid: [
        { left: 12, right: 62, top: 78, height: '58%' },
        { left: 12, right: 62, top: '76%', height: '16%' },
      ],
      xAxis: [
        {
          type: 'category',
          data: categories,
          boundaryGap: true,
          axisLabel: { show: false },
          axisLine: { lineStyle: { color: '#334155' } },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          gridIndex: 1,
          data: categories,
          boundaryGap: true,
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          axisLine: { lineStyle: { color: '#334155' } },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          position: 'right',
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
        },
        {
          gridIndex: 1,
          min: 0,
          max: 100,
          position: 'right',
          name: 'RSI',
          nameTextStyle: { color: '#94a3b8', fontSize: 10 },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: Math.max(0, 100 - (180 / Math.max(data.length, 1)) * 100),
          end: 100,
        },
      ],
      series,
    } as EChartsCoreOption;
  }, [data, showBB, showMA, srLevels, title, trades]);

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-dark-700 bg-dark-800/50"
        style={{ height }}
      >
        <p className="text-dark-400">No chart data available</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-dark-700 bg-dark-800/30">
      <EChart option={option} height={height} />
    </div>
  );
}
