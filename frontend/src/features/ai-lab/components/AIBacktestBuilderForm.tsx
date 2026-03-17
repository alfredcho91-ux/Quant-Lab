import type { Strategy } from '../../../types';
import type { Direction } from '../types';
import BuilderActionsSection from './builder/BuilderActionsSection';
import PromptSection from './builder/PromptSection';
import RiskSettingsSection from './builder/RiskSettingsSection';
import StrategyControlsSection from './builder/StrategyControlsSection';

interface AIBacktestBuilderFormProps {
  isKo: boolean;
  prompt: string;
  promptSamples: string[];
  selectedStrategyId: string;
  inferredStrategyId: string;
  runInterval: string;
  intervals: string[];
  direction: Direction;
  tp: number;
  sl: number;
  leverage: number;
  maxBars: number;
  strategies: Strategy[];
  runError: string | null;
  isGenerating: boolean;
  isRunning: boolean;
  onPromptChange: (value: string) => void;
  onPromptSampleSelect: (sample: string) => void;
  onStrategyChange: (strategyId: string) => void;
  onRunIntervalChange: (interval: string) => void;
  onDirectionChange: (direction: Direction) => void;
  onTpChange: (value: number) => void;
  onSlChange: (value: number) => void;
  onLeverageChange: (value: number) => void;
  onMaxBarsChange: (value: number) => void;
  onGenerateDraft: () => void;
  onRunBacktest: () => void;
}

export default function AIBacktestBuilderForm({
  isKo,
  prompt,
  promptSamples,
  selectedStrategyId,
  inferredStrategyId,
  runInterval,
  intervals,
  direction,
  tp,
  sl,
  leverage,
  maxBars,
  strategies,
  runError,
  isGenerating,
  isRunning,
  onPromptChange,
  onPromptSampleSelect,
  onStrategyChange,
  onRunIntervalChange,
  onDirectionChange,
  onTpChange,
  onSlChange,
  onLeverageChange,
  onMaxBarsChange,
  onGenerateDraft,
  onRunBacktest,
}: AIBacktestBuilderFormProps) {
  const directionDisabled = direction === 'Both';

  return (
    <div className="card p-5 space-y-4">
      <PromptSection
        isKo={isKo}
        prompt={prompt}
        promptSamples={promptSamples}
        onPromptChange={onPromptChange}
        onPromptSampleSelect={onPromptSampleSelect}
      />

      <StrategyControlsSection
        isKo={isKo}
        selectedStrategyId={selectedStrategyId}
        inferredStrategyId={inferredStrategyId}
        runInterval={runInterval}
        intervals={intervals}
        direction={direction}
        strategies={strategies}
        onStrategyChange={onStrategyChange}
        onRunIntervalChange={onRunIntervalChange}
        onDirectionChange={onDirectionChange}
      />

      <RiskSettingsSection
        isKo={isKo}
        tp={tp}
        sl={sl}
        leverage={leverage}
        maxBars={maxBars}
        onTpChange={onTpChange}
        onSlChange={onSlChange}
        onLeverageChange={onLeverageChange}
        onMaxBarsChange={onMaxBarsChange}
      />

      <BuilderActionsSection
        isKo={isKo}
        directionDisabled={directionDisabled}
        isGenerating={isGenerating}
        isRunning={isRunning}
        runError={runError}
        onGenerateDraft={onGenerateDraft}
        onRunBacktest={onRunBacktest}
      />
    </div>
  );
}
