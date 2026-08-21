import { formatCompactWon, formatPercent } from '../calculations';
import type { SummaryRow } from '../types';

interface CheckpointTableProps {
  isKo: boolean;
  initialCapital: number;
  rows: SummaryRow[];
}

export function CheckpointTable({ isKo, initialCapital, rows }: CheckpointTableProps) {
  return (
    <div className="card min-w-0 p-4 sm:p-5">
      <div className="mb-4 text-xs font-semibold uppercase text-dark-400">
        {isKo ? '구간별 자본 변화표' : 'Capital Checkpoints'}
      </div>
      <div className="max-w-full overflow-x-auto">
        <table className="w-full min-w-[680px] text-sm">
          <thead>
            <tr className="border-b border-dark-700 text-dark-400">
              <th className="px-3 py-2 text-left font-medium">{isKo ? '트레이드' : 'Trade'}</th>
              <th className="px-3 py-2 text-right font-medium">
                {isKo ? '복리 자본' : 'Compound Capital'}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {isKo ? '복리 수익률' : 'Compound ROI'}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {isKo ? '단리 자본' : 'Simple Capital'}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {isKo ? '단리 수익률' : 'Simple ROI'}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.trade} className="border-b border-dark-800 last:border-b-0">
                <td className="px-3 py-2 text-dark-300">
                  {row.trade}
                  {isKo ? '회' : ''}
                </td>
                <td
                  className={`px-3 py-2 text-right font-mono ${
                    row.compoundCapital >= initialCapital ? 'text-bull' : 'text-bear'
                  }`}
                >
                  ₩{formatCompactWon(row.compoundCapital)}
                </td>
                <td
                  className={`px-3 py-2 text-right font-mono ${
                    row.compoundRoi >= 0 ? 'text-bull' : 'text-bear'
                  }`}
                >
                  {formatPercent(row.compoundRoi)}
                </td>
                <td
                  className={`px-3 py-2 text-right font-mono ${
                    row.simpleCapital >= initialCapital ? 'text-bull' : 'text-bear'
                  }`}
                >
                  ₩{formatCompactWon(row.simpleCapital)}
                </td>
                <td
                  className={`px-3 py-2 text-right font-mono ${
                    row.simpleRoi >= 0 ? 'text-bull' : 'text-bear'
                  }`}
                >
                  {formatPercent(row.simpleRoi)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
