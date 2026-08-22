import { useCallback, useMemo } from 'react';
import { useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { getIndicatorProjection, getOHLCV, getVPVR } from '../api/client';
import { type TrendPriceLevel } from '../components/TrendPriceChart';
import type { Coin } from '../types';
import { getCompletedCandles } from '../utils/ohlcv';

export const PRICE_PROJECTION_INTERVALS = ['1h', '2h', '4h', '1d', '1w'] as const;
type PriceProjectionInterval = (typeof PRICE_PROJECTION_INTERVALS)[number];

export const TREND_PRICE_QUERY_OPTIONS = {
  staleTime: 60 * 60 * 1000,
  gcTime: 65 * 60 * 1000,
  refetchOnReconnect: false,
  retry: 1,
} as const;

const HOURLY_PROJECTION_QUERY_OPTIONS = {
  ...TREND_PRICE_QUERY_OPTIONS,
  refetchOnMount: 'always',
} as const;

export function useTrendPriceChart(
  coin: Coin,
  selectedInterval: string,
  { includeChart = true }: { includeChart?: boolean } = {},
) {
  const queryClient = useQueryClient();
  const selectedProjectionIndex = PRICE_PROJECTION_INTERVALS.indexOf(selectedInterval as PriceProjectionInterval);
  const projectionIntervals = useMemo(
    () =>
      selectedProjectionIndex >= 0
        ? PRICE_PROJECTION_INTERVALS
        : [...PRICE_PROJECTION_INTERVALS, selectedInterval],
    [selectedInterval, selectedProjectionIndex]
  );

  const vpvrQuery = useQuery({
    queryKey: ['vpvr', coin, selectedInterval],
    queryFn: () => getVPVR(coin, selectedInterval),
    ...TREND_PRICE_QUERY_OPTIONS,
  });

  const projectionQueries = useQueries({
    queries: projectionIntervals.map((interval) => ({
      queryKey: ['indicatorProjection', coin, interval],
      queryFn: () => getIndicatorProjection(coin, interval),
      ...HOURLY_PROJECTION_QUERY_OPTIONS,
    })),
  });

  const trendChartQuery = useQuery({
    queryKey: ['trendPriceChart', coin, selectedInterval],
    queryFn: async () => {
      const response = await getOHLCV(coin, selectedInterval, false, 201);
      return getCompletedCandles(response.data, 200);
    },
    enabled: includeChart,
    ...TREND_PRICE_QUERY_OPTIONS,
  });

  const selectedProjection = projectionQueries[
    selectedProjectionIndex >= 0 ? selectedProjectionIndex : PRICE_PROJECTION_INTERVALS.length
  ]?.data;
  const chartPriceLevels = useMemo<TrendPriceLevel[]>(
    () => {
      const levels = PRICE_PROJECTION_INTERVALS.flatMap((interval, index) => {
        const projection = projectionQueries[index]?.data;
        if (!projection) return [];

        return [
          {
            interval,
            price: projection.rsi_70_price,
            type: 'overbought' as const,
            isSelected: interval === selectedInterval,
          },
          {
            interval,
            price: projection.rsi_30_price,
            type: 'oversold' as const,
            isSelected: interval === selectedInterval,
          },
        ].filter((level) => Number.isFinite(level.price));
      });

      if (selectedProjectionIndex >= 0 || !selectedProjection) return levels;

      return [
        ...levels,
        {
          interval: selectedInterval,
          price: selectedProjection.rsi_70_price,
          type: 'overbought' as const,
          isSelected: true,
        },
        {
          interval: selectedInterval,
          price: selectedProjection.rsi_30_price,
          type: 'oversold' as const,
          isSelected: true,
        },
      ].filter((level) => Number.isFinite(level.price));
    },
    [projectionQueries, selectedInterval, selectedProjection, selectedProjectionIndex]
  );

  const refresh = useCallback(() => {
    const requests = [
      queryClient.refetchQueries({ queryKey: ['vpvr', coin, selectedInterval], exact: true }),
      ...projectionIntervals.map((interval) => queryClient.refetchQueries({
        queryKey: ['indicatorProjection', coin, interval],
        exact: true,
      })),
    ];
    if (includeChart) {
      requests.push(queryClient.refetchQueries({
        queryKey: ['trendPriceChart', coin, selectedInterval],
        exact: true,
      }));
    }
    void Promise.all(requests);
  }, [coin, includeChart, projectionIntervals, queryClient, selectedInterval]);

  const isProjectionFetching = projectionQueries.some((query) => query.isFetching);

  return {
    vpvrData: vpvrQuery.data,
    isVPVRLoading: vpvrQuery.isLoading,
    isVPVRFetching: vpvrQuery.isFetching,
    isVPVRError: vpvrQuery.isError,
    projectionQueries,
    selectedProjection,
    chartPriceLevels,
    trendChartData: trendChartQuery.data ?? [],
    isTrendChartLoading: trendChartQuery.isLoading,
    isTrendChartFetching: trendChartQuery.isFetching,
    isTrendChartError: trendChartQuery.isError,
    isRefreshing: vpvrQuery.isFetching || trendChartQuery.isFetching || isProjectionFetching,
    refresh,
  };
}
