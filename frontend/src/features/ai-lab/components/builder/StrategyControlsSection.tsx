import type { Strategy } from '../../../../types';
import type { Direction } from '../../types';

interface StrategyControlsSectionProps {
  isKo: boolean;
  selectedStrategyId: string;
  inferredStrategyId: string;
  runInterval: string;
  intervals: string[];
  direction: Direction;
  strategies: Strategy[];
  onStrategyChange: (strategyId: string) => void;
  onRunIntervalChange: (interval: string) => void;
  onDirectionChange: (direction: Direction) => void;
}

export default function StrategyControlsSection({
  isKo,
  selectedStrategyId,
  inferredStrategyId,
  runInterval,
  intervals,
  direction,
  strategies,
  onStrategyChange,
  onRunIntervalChange,
  onDirectionChange,
}: StrategyControlsSectionProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div>
        <label className="block text-sm text-dark-300 mb-2">
          {isKo ? '전략 템플릿' : 'Strategy Template'}
        </label>
        <select
          value={selectedStrategyId}
          onChange={(event) => onStrategyChange(event.target.value)}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
        >
          {strategies.map((strategy) => (
            <option key={strategy.id} value={strategy.id}>
              {isKo ? strategy.name_ko : strategy.name_en}
            </option>
          ))}
        </select>
        <div className="text-[11px] text-dark-500 mt-1">
          {isKo ? 'AI 추천' : 'AI suggestion'}:{' '}
          <span className="text-cyan-300">{inferredStrategyId}</span>
        </div>
      </div>

      <div>
        <label className="block text-sm text-dark-300 mb-2">
          {isKo ? '실행 봉 주기' : 'Run Interval'}
        </label>
        <select
          value={runInterval}
          onChange={(event) => onRunIntervalChange(event.target.value)}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
        >
          {intervals.map((interval) => (
            <option key={interval} value={interval}>
              {interval}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-dark-300 mb-2">
          {isKo ? '방향' : 'Direction'}
        </label>
        <select
          value={direction}
          onChange={(event) => onDirectionChange(event.target.value as Direction)}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
        >
          <option value="Long">Long</option>
          <option value="Short">Short</option>
          <option value="Both">{isKo ? '양방향' : 'Both'}</option>
        </select>
      </div>
    </div>
  );
}
