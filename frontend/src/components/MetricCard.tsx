// Metric Card component
import { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export default function MetricCard({
  label,
  value,
  icon,
  trend,
  className = '',
}: MetricCardProps) {
  const trendColor =
    trend === 'up'
      ? 'text-bull'
      : trend === 'down'
      ? 'text-bear'
      : 'text-dark-200';

  return (
    <div className={`metric-card ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="metric-label">{label}</span>
        {icon && <span className="text-dark-400">{icon}</span>}
      </div>
      <div className={`metric-value ${trendColor}`}>{value}</div>
    </div>
  );
}

