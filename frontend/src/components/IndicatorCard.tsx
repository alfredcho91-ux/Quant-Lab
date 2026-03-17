interface IndicatorCardProps {
  label: string;
  value: number | null;
  sub?: string;
  bullish: boolean | null;
}

export function IndicatorCard({
  label,
  value,
  sub,
  bullish,
}: IndicatorCardProps) {
  const bg = bullish === true ? 'bg-primary-500/10 border-primary-500/30' : bullish === false ? 'bg-red-500/10 border-red-500/30' : 'bg-dark-800 border-dark-600';
  const text = bullish === true ? 'text-primary-400' : bullish === false ? 'text-red-400' : 'text-dark-300';
  return (
    <div className={`rounded-lg border p-3 ${bg}`}>
      <div className="text-xs text-dark-500 uppercase tracking-wide mb-0.5">{label}</div>
      <div className={`text-lg font-bold font-mono ${text}`}>
        {value != null ? (typeof value === 'number' && value % 1 !== 0 ? value.toFixed(2) : String(value)) : '—'}
      </div>
      {sub != null && <div className="text-xs text-dark-500 mt-1">{sub}</div>}
    </div>
  );
}
