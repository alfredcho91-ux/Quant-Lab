import { metricToneClass } from '../calculations';
import type { RiskRow } from '../types';

export function RiskTable({ isKo, rows }: { isKo: boolean; rows: RiskRow[] }) {
  return (
    <div className="card min-w-0 p-4 sm:p-5">
      <div className="mb-4 text-xs font-semibold uppercase text-dark-400">
        {isKo ? '연속 손절 위험 분석' : 'Losing Streak Risk'}
      </div>
      <div className="max-w-full overflow-x-auto">
        <table className="w-full min-w-[420px] text-sm">
          <thead>
            <tr className="border-b border-dark-700 text-dark-400">
              <th className="px-3 py-2 text-left font-medium">
                {isKo ? '연속 손절' : 'Streak'}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {isKo ? '발생 확률' : 'Probability'}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {isKo ? '자본 손실' : 'Capital Loss'}
              </th>
              <th className="px-3 py-2 text-right font-medium">{isKo ? '위험도' : 'Risk'}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.streak} className="border-b border-dark-800 last:border-b-0">
                <td className="px-3 py-2 text-dark-300">
                  {row.streak}
                  {isKo ? '연속' : 'x'}
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {row.probability.toFixed(2)}%
                </td>
                <td className={`px-3 py-2 text-right font-mono ${metricToneClass[row.tone]}`}>
                  {row.capitalLoss.toFixed(1)}%
                </td>
                <td className="px-3 py-2 text-right">
                  <span
                    className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ${
                      row.tone === 'positive'
                        ? 'bg-bull/15 text-bull'
                        : row.tone === 'warning'
                          ? 'bg-warning/15 text-warning'
                          : 'bg-bear/15 text-bear'
                    }`}
                  >
                    {row.label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
