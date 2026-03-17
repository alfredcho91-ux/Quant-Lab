interface RiskSettingsSectionProps {
  isKo: boolean;
  tp: number;
  sl: number;
  leverage: number;
  maxBars: number;
  onTpChange: (value: number) => void;
  onSlChange: (value: number) => void;
  onLeverageChange: (value: number) => void;
  onMaxBarsChange: (value: number) => void;
}

export default function RiskSettingsSection({
  isKo,
  tp,
  sl,
  leverage,
  maxBars,
  onTpChange,
  onSlChange,
  onLeverageChange,
  onMaxBarsChange,
}: RiskSettingsSectionProps) {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-sm text-dark-300 mb-2">TP %</label>
          <input
            type="number"
            value={tp}
            onChange={(event) => onTpChange(parseFloat(event.target.value) || 0)}
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm text-dark-300 mb-2">SL %</label>
          <input
            type="number"
            value={sl}
            onChange={(event) => onSlChange(parseFloat(event.target.value) || 0)}
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm text-dark-300 mb-2">
            {isKo ? '레버리지 (x)' : 'Leverage (x)'}
          </label>
          <input
            type="number"
            min={1}
            max={125}
            value={leverage}
            onChange={(event) =>
              onLeverageChange(Math.max(1, Math.min(125, Number(event.target.value) || 1)))
            }
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
          />
        </div>
      </div>

      <div className="text-xs text-dark-400">
        {isKo ? '데이터 소스: CSV 고정' : 'Data source: CSV fixed'}
      </div>

      <div>
        <label className="block text-sm text-dark-300 mb-2">
          {isKo ? '최대 보유 봉' : 'Max Holding Bars'}
        </label>
        <input
          type="number"
          value={maxBars}
          onChange={(event) => onMaxBarsChange(parseInt(event.target.value, 10) || 1)}
          className="w-full md:w-48 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
        />
      </div>
    </>
  );
}
