import { useEffect, useMemo, useRef } from 'react';
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
  createChart,
  type CandlestickData,
  type UTCTimestamp,
} from 'lightweight-charts';

import type { IndicatorProjection, OHLCV, VPVRData } from '../types';
import { CHART_BOTTOM_AXIS, VPVRProfile } from './VPVRProfile';

export interface TrendPriceLevel {
  interval: string;
  price: number;
  type: 'overbought' | 'oversold';
  isSelected?: boolean;
}

interface TrendPriceChartProps {
  data: OHLCV[];
  vpvr?: VPVRData;
  vwaps?: IndicatorProjection;
  priceLevels: TrendPriceLevel[];
  verticalZoom: number;
  isKo: boolean;
  height?: number;
  baseHalfRange?: number;
  baseHalfRangePercent?: number;
}

interface ReferenceLine {
  key: string;
  label: string;
  price: number;
  color: string;
  width: 1 | 2 | 3 | 4;
  style: LineStyle;
  labelPosition: number;
  selected?: boolean;
}

const VWAP_COLORS: Record<string, string> = {
  day: '#38bdf8',
  week: '#a78bfa',
  month: '#f59e0b',
  quarter: '#fb7185',
  year: '#e2e8f0',
  rolling: '#22c55e',
};

const VWAP_LABELS: Record<string, string> = {
  day: '일간 VWAP',
  week: '주간 VWAP',
  month: '월간 VWAP',
  quarter: '분기 VWAP',
  year: '연간 VWAP',
};

const VWAP_ENGLISH_LABELS: Record<string, string> = {
  day: 'Daily VWAP',
  week: 'Weekly VWAP',
  month: 'Monthly VWAP',
  quarter: 'Quarterly VWAP',
  year: 'Yearly VWAP',
};

const RSI_TARGET_COLORS: Record<TrendPriceLevel['type'], Record<string, string>> = {
  overbought: {
    '1h': '#fda4af',
    '2h': '#fb7185',
    '4h': '#e11d48',
    '1d': '#be123c',
  },
  oversold: {
    '1h': '#7dd3fc',
    '2h': '#38bdf8',
    '4h': '#0ea5e9',
    '1d': '#0369a1',
  },
};

const LABEL_POSITIONS: Record<string, number> = {
  '1h': 18,
  '2h': 39,
  '4h': 61,
  '1d': 82,
};

function formatPrice(value: number): string {
  const digits = value >= 1_000 ? 0 : value >= 1 ? 2 : 4;
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function priceLevelLabel(level: TrendPriceLevel, isKo: boolean): string {
  const state = level.type === 'overbought'
    ? isKo ? '과매수' : 'Overbought'
    : isKo ? '과매도' : 'Oversold';
  const interval = isKo ? level.interval.replace('d', 'D') : level.interval;
  return `${interval} ${state}`;
}

function priceLevelColor(level: TrendPriceLevel): string {
  return RSI_TARGET_COLORS[level.type][level.interval] ??
    (level.type === 'overbought' ? '#fb7185' : '#38bdf8');
}

function priceLevelStyle(level: TrendPriceLevel): LineStyle {
  if (level.interval === '1h') return LineStyle.Dotted;
  if (level.interval === '4h') return LineStyle.Solid;
  if (level.interval === '1d') return LineStyle.LargeDashed;
  return LineStyle.Dashed;
}

export function TrendPriceChart({
  data,
  vpvr,
  vwaps,
  priceLevels,
  verticalZoom,
  isKo,
  height = 500,
  baseHalfRange,
  baseHalfRangePercent,
}: TrendPriceChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const { priceAxisMin, priceAxisMax } = useMemo(() => {
    const values = [
      ...data.flatMap((row) => [row.low, row.high]),
      ...priceLevels.map((level) => level.price),
      ...(vwaps?.vwaps.flatMap(({ value }) => value == null ? [] : [value]) ?? []),
      ...(vwaps?.rolling_vwaps.flatMap(({ value }) => value == null ? [] : [value]) ?? []),
      ...(vpvr ? [vpvr.poc_price_low, vpvr.poc_price_high, vpvr.value_area_low, vpvr.value_area_high] : []),
    ].filter(Number.isFinite);

    if (values.length === 0) return { priceAxisMin: 0, priceAxisMax: 1 };
    const rawMin = Math.min(...values);
    const rawMax = Math.max(...values);
    const padding = Math.max((rawMax - rawMin) * 0.06, 1);
    const fullMin = rawMin - padding;
    const fullMax = rawMax + padding;
    const currentPrice = data[data.length - 1]?.close ?? (fullMin + fullMax) / 2;
    const halfRange = baseHalfRange ?? (baseHalfRangePercent ? currentPrice * baseHalfRangePercent : null);
    const fullRange = halfRange ? halfRange * 2 : fullMax - fullMin;
    const zoomedRange = fullRange / verticalZoom;
    const centeredMin = currentPrice - zoomedRange / 2;
    const centeredMax = currentPrice + zoomedRange / 2;

    return {
      priceAxisMin: halfRange ? Math.max(0, centeredMin) : verticalZoom === 1 ? fullMin : centeredMin,
      priceAxisMax: halfRange && centeredMin < 0 ? zoomedRange : centeredMax,
    };
  }, [baseHalfRange, baseHalfRangePercent, data, priceLevels, verticalZoom, vpvr, vwaps]);

  const referenceLines = useMemo<ReferenceLine[]>(() => {
    const lines: ReferenceLine[] = [];
    if (vpvr) {
      lines.push(
        {
          key: 'poc',
          label: isKo ? 'POC 매물대' : 'POC volume',
          price: (vpvr.poc_price_low + vpvr.poc_price_high) / 2,
          color: '#fbbf24',
          width: 2,
          style: LineStyle.Solid,
          labelPosition: 50,
        },
        {
          key: 'vah',
          label: isKo ? 'VAH 상단' : 'VAH high',
          price: vpvr.value_area_high,
          color: '#60a5fa',
          width: 1,
          style: LineStyle.Dotted,
          labelPosition: 28,
        },
        {
          key: 'val',
          label: isKo ? 'VAL 하단' : 'VAL low',
          price: vpvr.value_area_low,
          color: '#60a5fa',
          width: 1,
          style: LineStyle.Dotted,
          labelPosition: 72,
        },
      );
    }

    const vwapLabels = isKo ? VWAP_LABELS : VWAP_ENGLISH_LABELS;
    vwaps?.vwaps.forEach(({ anchor, value }, index) => {
      if (value == null) return;
      lines.push({
        key: `vwap-${anchor}`,
        label: vwapLabels[anchor] ?? `VWAP ${anchor}`,
        price: value,
        color: VWAP_COLORS[anchor],
        width: 1,
        style: LineStyle.Dashed,
        labelPosition: [20, 40, 60, 80][index] ?? 50,
      });
    });
    vwaps?.rolling_vwaps.forEach(({ window, value }, index) => {
      if (value == null) return;
      lines.push({
        key: `rolling-${window}`,
        label: isKo ? `${window}봉 VWAP` : `${window}-bar VWAP`,
        price: value,
        color: VWAP_COLORS.rolling,
        width: 1,
        style: LineStyle.Dashed,
        labelPosition: 84 - index * 8,
      });
    });
    priceLevels.forEach((level) => {
      lines.push({
        key: `${level.interval}-${level.type}`,
        label: priceLevelLabel(level, isKo),
        price: level.price,
        color: priceLevelColor(level),
        width: level.isSelected ? 2 : 1,
        style: priceLevelStyle(level),
        labelPosition: LABEL_POSITIONS[level.interval] ?? 50,
        selected: level.isSelected,
      });
    });
    return lines;
  }, [isKo, priceLevels, vpvr, vwaps]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || data.length === 0) return undefined;

    const chart = createChart(container, {
      width: container.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#111827' },
        textColor: '#94a3b8',
        attributionLogo: true,
      },
      grid: {
        vertLines: { color: 'rgba(51, 65, 85, 0.35)' },
        horzLines: { color: 'rgba(51, 65, 85, 0.42)' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: {
        borderColor: '#334155',
        scaleMargins: { top: 0, bottom: 0 },
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 4,
      },
      handleScroll: true,
      handleScale: true,
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#f87171',
      borderUpColor: '#22c55e',
      borderDownColor: '#f87171',
      wickUpColor: '#4ade80',
      wickDownColor: '#fca5a5',
      priceLineVisible: false,
      autoscaleInfoProvider: () => ({
        priceRange: { minValue: priceAxisMin, maxValue: priceAxisMax },
      }),
    });

    const candleData: CandlestickData<UTCTimestamp>[] = data.map((row) => ({
      time: Math.floor(row.open_time / 1000) as UTCTimestamp,
      open: row.open,
      high: row.high,
      low: row.low,
      close: row.close,
    }));
    series.setData(candleData);

    referenceLines.forEach((line) => {
      series.createPriceLine({
        price: line.price,
        color: line.color,
        lineWidth: line.width,
        lineStyle: line.style,
        axisLabelVisible: true,
        title: '',
      });
    });

    const overlay = document.createElement('div');
    overlay.className = 'pointer-events-none absolute inset-0 overflow-hidden';
    container.appendChild(overlay);

    const valueArea = vpvr ? document.createElement('div') : null;
    if (valueArea) {
      valueArea.className = 'absolute left-0 right-0 bg-blue-500/10';
      overlay.appendChild(valueArea);
    }

    const legend = document.createElement('div');
    legend.className = 'absolute left-2 top-1 z-20 text-[10px] font-mono text-dark-300';
    overlay.appendChild(legend);

    const labelElements = referenceLines.map((line) => {
      const element = document.createElement('span');
      element.textContent = `${line.label} ${formatPrice(line.price)}`;
      element.className = 'absolute z-10 whitespace-nowrap text-[9px] font-semibold sm:text-[10px]';
      element.style.color = line.color;
      element.style.left = `${Math.min(line.labelPosition, 78)}%`;
      element.style.transform = 'translate(-50%, -50%)';
      element.style.textShadow = '0 0 3px #111827, 0 0 3px #111827, 0 0 4px #111827';
      element.style.opacity = line.selected === false ? '0.8' : '1';
      overlay.appendChild(element);
      return { element, line };
    });

    const setLegend = (bar: CandlestickData<UTCTimestamp> | undefined) => {
      if (!bar) return;
      legend.textContent = `O ${formatPrice(bar.open)}  H ${formatPrice(bar.high)}  L ${formatPrice(bar.low)}  C ${formatPrice(bar.close)}`;
    };
    setLegend(candleData[candleData.length - 1]);

    const updateOverlay = () => {
      const visibleLabels: Array<{ element: HTMLSpanElement; line: ReferenceLine; y: number }> = [];
      labelElements.forEach(({ element, line }) => {
        const y = series.priceToCoordinate(line.price);
        element.style.display = y == null || y < 0 || y > height - CHART_BOTTOM_AXIS ? 'none' : 'block';
        if (y != null) {
          element.style.top = `${y}px`;
          element.style.left = `${Math.min(line.labelPosition, 78)}%`;
          visibleLabels.push({ element, line, y });
        }
      });

      const clusters: typeof visibleLabels[] = [];
      visibleLabels
        .sort((a, b) => a.y - b.y)
        .forEach((item) => {
          const cluster = clusters[clusters.length - 1];
          if (cluster && Math.abs(item.y - cluster[cluster.length - 1].y) <= 12) {
            cluster.push(item);
          } else {
            clusters.push([item]);
          }
        });
      clusters.forEach((cluster) => {
        if (cluster.length < 2) return;
        cluster
          .sort((a, b) => a.line.labelPosition - b.line.labelPosition)
          .forEach(({ element }, index) => {
            const position = 8 + (index / Math.max(cluster.length - 1, 1)) * 68;
            element.style.left = `${position}%`;
          });
      });
      if (valueArea && vpvr) {
        const top = series.priceToCoordinate(vpvr.value_area_high);
        const bottom = series.priceToCoordinate(vpvr.value_area_low);
        valueArea.style.display = top == null || bottom == null ? 'none' : 'block';
        if (top != null && bottom != null) {
          valueArea.style.top = `${top}px`;
          valueArea.style.height = `${Math.max(1, bottom - top)}px`;
        }
      }
    };

    chart.subscribeCrosshairMove((param) => {
      const bar = param.seriesData.get(series) as CandlestickData<UTCTimestamp> | undefined;
      setLegend(bar ?? candleData[candleData.length - 1]);
      updateOverlay();
    });
    chart.timeScale().subscribeVisibleLogicalRangeChange(updateOverlay);
    chart.timeScale().fitContent();
    requestAnimationFrame(updateOverlay);

    const resizeObserver = new ResizeObserver(([entry]) => {
      chart.resize(Math.floor(entry.contentRect.width), height);
      requestAnimationFrame(updateOverlay);
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      overlay.remove();
      chart.remove();
    };
  }, [data, height, priceAxisMax, priceAxisMin, referenceLines, vpvr]);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center border border-dark-700 bg-dark-800/50" style={{ height }}>
        <p className="text-sm text-dark-400">{isKo ? '차트 데이터를 불러오지 못했습니다.' : 'Chart data is unavailable.'}</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden border border-dark-700 bg-dark-800/30">
      <div className="flex">
        <div className="min-w-0 flex-1">
          <div ref={containerRef} className="relative w-full" style={{ height }} />
        </div>
        {vpvr && (
          <VPVRProfile
            vpvr={vpvr}
            height={height}
            isKo={isKo}
            priceAxisMin={priceAxisMin}
            priceAxisMax={priceAxisMax}
          />
        )}
      </div>
    </div>
  );
}
