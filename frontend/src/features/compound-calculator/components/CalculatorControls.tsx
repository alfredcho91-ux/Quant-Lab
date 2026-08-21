interface SliderControlProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  output: string;
  onChange: (value: number) => void;
}

function SliderControl({
  label,
  value,
  min,
  max,
  step,
  output,
  onChange,
}: SliderControlProps) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <label className="block text-sm text-dark-400">{label}</label>
        <span className="min-w-[64px] text-right font-mono text-sm text-dark-100">{output}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-2 h-2 w-full cursor-pointer accent-primary-500"
      />
    </div>
  );
}

interface CalculatorControlsProps {
  isKo: boolean;
  capital: number;
  trades: number;
  risk: number;
  rr: number;
  winRate: number;
  slippage: number;
  setCapital: (value: number) => void;
  setTrades: (value: number) => void;
  setRisk: (value: number) => void;
  setRr: (value: number) => void;
  setWinRate: (value: number) => void;
  setSlippage: (value: number) => void;
}

export function CalculatorControls(props: CalculatorControlsProps) {
  const { isKo } = props;
  return (
    <div className="grid min-w-0 gap-4 xl:grid-cols-2">
      <div className="card min-w-0 p-4 sm:p-5">
        <div className="mb-5 text-xs font-semibold uppercase text-dark-400">
          {isKo ? '기본 설정' : 'Base Settings'}
        </div>
        <div className="space-y-5">
          <div>
            <label className="mb-2 block text-sm text-dark-400">
              {isKo ? '초기 자본' : 'Initial Capital'}
            </label>
            <input
              type="number"
              min={0}
              step={1_000_000}
              value={props.capital}
              onChange={(event) => props.setCapital(Number(event.target.value))}
              className="w-full"
            />
          </div>
          <SliderControl
            label={isKo ? '총 트레이드 횟수' : 'Total Trades'}
            value={props.trades}
            min={10}
            max={500}
            step={10}
            output={`${props.trades}${isKo ? '회' : ''}`}
            onChange={props.setTrades}
          />
          <SliderControl
            label={isKo ? '트레이드당 리스크' : 'Risk per Trade'}
            value={props.risk}
            min={0.5}
            max={10}
            step={0.5}
            output={`${props.risk.toFixed(1)}%`}
            onChange={props.setRisk}
          />
        </div>
      </div>

      <div className="card min-w-0 p-4 sm:p-5">
        <div className="mb-5 text-xs font-semibold uppercase text-dark-400">
          {isKo ? '손익비 & 승률' : 'R:R & Win Rate'}
        </div>
        <div className="space-y-5">
          <SliderControl
            label={isKo ? '손익비 (이익 / 손실)' : 'Risk Reward Ratio'}
            value={props.rr}
            min={0.5}
            max={5}
            step={0.1}
            output={props.rr.toFixed(1)}
            onChange={props.setRr}
          />
          <SliderControl
            label={isKo ? '승률' : 'Win Rate'}
            value={props.winRate}
            min={20}
            max={80}
            step={1}
            output={`${props.winRate}%`}
            onChange={props.setWinRate}
          />
          <SliderControl
            label={isKo ? '손절 슬리피지' : 'Stop Slippage'}
            value={props.slippage}
            min={0}
            max={1}
            step={0.05}
            output={`${props.slippage.toFixed(2)}%`}
            onChange={props.setSlippage}
          />
        </div>
      </div>
    </div>
  );
}
