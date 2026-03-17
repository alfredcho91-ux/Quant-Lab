import { lazy, Suspense } from 'react';
import type { ChartProps } from './Chart';
import { SkeletonChart } from './Skeleton';

const Chart = lazy(() => import('./Chart'));

export default function LazyChart(props: ChartProps) {
  return (
    <Suspense fallback={<SkeletonChart />}>
      <Chart {...props} />
    </Suspense>
  );
}
