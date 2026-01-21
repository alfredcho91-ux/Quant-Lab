// Candlestick Chart component using Plotly
import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { OHLCV, Trade, SRLevel } from '../types';

interface ChartProps {
  data: OHLCV[];
  trades?: Trade[];
  srLevels?: SRLevel[];
  title?: string;
  showBB?: boolean;
  showMA?: boolean;
  height?: number;
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
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const traces: Plotly.Data[] = [];

    // Candlestick
    traces.push({
      type: 'candlestick',
      x: data.map((d) => d.open_dt),
      open: data.map((d) => d.open),
      high: data.map((d) => d.high),
      low: data.map((d) => d.low),
      close: data.map((d) => d.close),
      name: 'Price',
      increasing: { line: { color: '#26a69a' } },
      decreasing: { line: { color: '#ef5350' } },
      xaxis: 'x',
      yaxis: 'y',
    });

    // EMA
    if (showMA && data[0]?.EMA_main !== undefined) {
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: data.map((d) => d.open_dt),
        y: data.map((d) => d.EMA_main ?? null),
        name: 'EMA 200',
        line: { color: '#fbbf24', width: 1 },
        xaxis: 'x',
        yaxis: 'y',
      });
    }

    // SMA 1
    if (showMA && data[0]?.SMA_1 !== undefined) {
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: data.map((d) => d.open_dt),
        y: data.map((d) => d.SMA_1 ?? null),
        name: 'MA 20',
        line: { color: '#00bcd4', width: 1 },
        xaxis: 'x',
        yaxis: 'y',
      });
    }

    // SMA 2
    if (showMA && data[0]?.SMA_2 !== undefined) {
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: data.map((d) => d.open_dt),
        y: data.map((d) => d.SMA_2 ?? null),
        name: 'MA 60',
        line: { color: '#ff9800', width: 1 },
        xaxis: 'x',
        yaxis: 'y',
      });
    }

    // Bollinger Bands
    if (showBB && data[0]?.BB_Up !== undefined) {
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: data.map((d) => d.open_dt),
        y: data.map((d) => d.BB_Up ?? null),
        name: 'BB Upper',
        line: { color: '#64748b', dash: 'dot', width: 1 },
        xaxis: 'x',
        yaxis: 'y',
      });
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: data.map((d) => d.open_dt),
        y: data.map((d) => d.BB_Low ?? null),
        name: 'BB Lower',
        line: { color: '#64748b', dash: 'dot', width: 1 },
        xaxis: 'x',
        yaxis: 'y',
      });
    }

    // RSI subplot
    if (data[0]?.RSI !== undefined) {
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: data.map((d) => d.open_dt),
        y: data.map((d) => d.RSI ?? null),
        name: 'RSI(14)',
        line: { color: '#9fa8da', width: 1 },
        xaxis: 'x2',
        yaxis: 'y2',
      });
    }

    // Trade markers
    if (trades.length > 0) {
      const longEntries = trades.filter((t) => t.Direction === 'Long');
      const shortEntries = trades.filter((t) => t.Direction === 'Short');
      const wins = trades.filter((t) => t.PnL > 0);
      const losses = trades.filter((t) => t.PnL <= 0);

      if (longEntries.length > 0) {
        traces.push({
          type: 'scatter',
          mode: 'markers',
          x: longEntries.map((t) => t['Entry Time']),
          y: longEntries.map((t) => t['Entry Price']),
          name: 'Long Entry',
          marker: { symbol: 'triangle-up', color: '#00bcd4', size: 12 },
          xaxis: 'x',
          yaxis: 'y',
        });
      }

      if (shortEntries.length > 0) {
        traces.push({
          type: 'scatter',
          mode: 'markers',
          x: shortEntries.map((t) => t['Entry Time']),
          y: shortEntries.map((t) => t['Entry Price']),
          name: 'Short Entry',
          marker: { symbol: 'triangle-down', color: '#e040fb', size: 12 },
          xaxis: 'x',
          yaxis: 'y',
        });
      }

      if (wins.length > 0) {
        traces.push({
          type: 'scatter',
          mode: 'markers',
          x: wins.map((t) => t['Exit Time']),
          y: wins.map((t) => t['Exit Price']),
          name: 'Win',
          marker: { symbol: 'diamond', color: '#00e676', size: 9 },
          xaxis: 'x',
          yaxis: 'y',
        });
      }

      if (losses.length > 0) {
        traces.push({
          type: 'scatter',
          mode: 'markers',
          x: losses.map((t) => t['Exit Time']),
          y: losses.map((t) => t['Exit Price']),
          name: 'Loss',
          marker: { symbol: 'x', color: '#ff1744', size: 9 },
          xaxis: 'x',
          yaxis: 'y',
        });
      }
    }

    return traces;
  }, [data, trades, showBB, showMA]);

  const layout = useMemo<Partial<Plotly.Layout>>(() => {
    const shapes: Partial<Plotly.Shape>[] = [];

    // RSI overbought/oversold lines
    shapes.push(
      { type: 'line', x0: 0, x1: 1, y0: 70, y1: 70, xref: 'paper', yref: 'y2', line: { color: '#ef5350', dash: 'dot', width: 1 } },
      { type: 'line', x0: 0, x1: 1, y0: 30, y1: 30, xref: 'paper', yref: 'y2', line: { color: '#26a69a', dash: 'dot', width: 1 } }
    );

    // SR Levels
    srLevels.forEach((level) => {
      const color =
        level.kind === 'support'
          ? '#4caf50'
          : level.kind === 'resistance'
          ? '#ef5350'
          : '#ffb300';
      shapes.push({
        type: 'line',
        x0: 0,
        x1: 1,
        y0: level.price,
        y1: level.price,
        xref: 'paper',
        yref: 'y',
        line: { color, dash: 'dot', width: 1 },
      });
    });

    return {
      paper_bgcolor: 'rgba(15, 23, 42, 0)',
      plot_bgcolor: 'rgba(30, 41, 59, 0.5)',
      font: { color: '#94a3b8', family: 'Pretendard, sans-serif' },
      title: {
        text: title,
        font: { size: 16, color: '#f1f5f9' },
        x: 0.02,
        xanchor: 'left',
      },
      xaxis: {
        domain: [0, 1],
        anchor: 'y',
        rangeslider: { visible: false },
        gridcolor: 'rgba(51, 65, 85, 0.5)',
        linecolor: '#334155',
        tickfont: { size: 10 },
      },
      yaxis: {
        domain: [0.32, 1],
        anchor: 'x',
        gridcolor: 'rgba(51, 65, 85, 0.5)',
        linecolor: '#334155',
        side: 'right',
        tickfont: { size: 10 },
      },
      xaxis2: {
        domain: [0, 1],
        anchor: 'y2',
        gridcolor: 'rgba(51, 65, 85, 0.5)',
        linecolor: '#334155',
        tickfont: { size: 10 },
      },
      yaxis2: {
        domain: [0, 0.28],
        anchor: 'x2',
        gridcolor: 'rgba(51, 65, 85, 0.5)',
        linecolor: '#334155',
        side: 'right',
        tickfont: { size: 10 },
        range: [0, 100],
        title: { text: 'RSI', font: { size: 10 } },
      },
      shapes,
      margin: { l: 10, r: 60, t: 40, b: 40 },
      legend: {
        x: 0.02,
        y: 0.98,
        bgcolor: 'rgba(15, 23, 42, 0.7)',
        bordercolor: '#334155',
        borderwidth: 1,
        font: { size: 10 },
      },
      dragmode: 'pan',
      hovermode: 'x unified',
    };
  }, [title, srLevels]);

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-dark-800/50 rounded-xl border border-dark-700"
        style={{ height }}
      >
        <p className="text-dark-400">No chart data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl overflow-hidden border border-dark-700 bg-dark-800/30">
      <Plot
        data={chartData}
        layout={layout}
        config={{
          scrollZoom: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['autoScale2d', 'lasso2d', 'select2d'],
          responsive: true,
        }}
        style={{ width: '100%', height }}
      />
    </div>
  );
}

