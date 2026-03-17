/** K·D 두 선을 함께 그리는 Slow Stochastic 차트 */
export function StochMiniChart({
  tk,
  vk,
  vd,
  yRefs = [],
  height = 100,
}: {
  tk: string[];
  vk: number[];
  vd?: number[];
  yRefs?: number[];
  height?: number;
}) {
  const validK = (vk || []).filter((x) => typeof x === 'number' && !Number.isNaN(x));
  const validD = (vd || []).filter((x) => typeof x === 'number' && !Number.isNaN(x));
  const hasK = (tk?.length ?? 0) > 0 && validK.length > 0;
  if (!hasK) return <div className="h-12 bg-dark-800/50 rounded flex items-center justify-center text-dark-500 text-xs">No data</div>;

  const allV = [...validK, ...validD];
  const min = Math.min(...allV);
  const max = Math.max(...allV);
  const range = max - min || 1;
  const h = height - 16;
  const toY = (val: number) => 12 + (max - val) / range * (h - 8);

  const ptsK = vk.map((val, i) => {
    const x = (i / (vk.length - 1 || 1)) * 100;
    const y = typeof val === 'number' && !Number.isNaN(val) ? toY(val) : 12 + h / 2;
    return `${x},${y}`;
  }).join(' ');

  const vdArr = vd || [];
  const ptsD = vdArr.map((val, i) => {
    const x = (i / (vdArr.length - 1 || 1)) * 100;
    const y = typeof val === 'number' && !Number.isNaN(val) ? toY(val) : 12 + h / 2;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full block" preserveAspectRatio="none" style={{ height: `${height}px` }}>
      <polyline fill="none" stroke="#3b82f6" strokeWidth="1" vectorEffect="non-scaling-stroke" points={ptsK} />
      {vdArr.length > 0 && <polyline fill="none" stroke="#f59e0b" strokeWidth="1" vectorEffect="non-scaling-stroke" strokeDasharray="3,2" points={ptsD} />}
      {yRefs.map((r, i) => (
        <line key={i} x1="0" y1={toY(r)} x2="100" y2={toY(r)} stroke="#6b7280" strokeWidth="0.5" strokeDasharray="2,2" />
      ))}
    </svg>
  );
}
