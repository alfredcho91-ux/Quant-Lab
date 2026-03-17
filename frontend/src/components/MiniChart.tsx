interface MiniChartProps {
  t: string[];
  v: number[];
  yRefs?: number[];
  height?: number;
}

export function MiniChart({ t, v, yRefs = [], height = 80 }: MiniChartProps) {
  const validV = (v || []).filter((x) => typeof x === 'number' && !Number.isNaN(x));
  if (!t?.length || validV.length === 0) return <div className="h-12 bg-dark-800/50 rounded flex items-center justify-center text-dark-500 text-xs">No data</div>;
  const min = Math.min(...validV);
  const max = Math.max(...validV);
  const range = max - min || 1;
  const h = height - 16;
  const pts = v.map((val, i) => {
    const x = (i / (v.length - 1 || 1)) * 100;
    const y = typeof val === 'number' && !Number.isNaN(val) ? 12 + (max - val) / range * (h - 8) : 12 + h / 2;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full block" preserveAspectRatio="none" style={{ height: `${height}px` }}>
      <polyline fill="none" stroke="#3b82f6" strokeWidth="1" vectorEffect="non-scaling-stroke" points={pts} />
      {yRefs.map((r, i) => {
        const y = 12 + (max - r) / range * (h - 8);
        const isMid = r === 50;
        const isBand = r === 30 || r === 70;
        return (
          <line
            key={i}
            x1="0"
            y1={y}
            x2="100"
            y2={y}
            stroke={isMid ? '#9ca3af' : '#6b7280'}
            strokeWidth={isBand ? '1.2' : '0.7'}
            strokeDasharray={isMid ? undefined : '2,2'}
          />
        );
      })}
    </svg>
  );
}
