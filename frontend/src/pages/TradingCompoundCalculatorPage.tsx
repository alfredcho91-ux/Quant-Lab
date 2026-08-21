import { Calculator } from 'lucide-react';
import { CalculatorControls } from '../features/compound-calculator/components/CalculatorControls';
import { CalculatorMetrics } from '../features/compound-calculator/components/CalculatorMetrics';
import { CheckpointTable } from '../features/compound-calculator/components/CheckpointTable';
import { EvHeatmap } from '../features/compound-calculator/components/EvHeatmap';
import { GrowthChart } from '../features/compound-calculator/components/GrowthChart';
import { RiskTable } from '../features/compound-calculator/components/RiskTable';
import { useCompoundCalculator } from '../features/compound-calculator/hooks/useCompoundCalculator';
import { useLanguage } from '../store/useStore';

export default function TradingCompoundCalculatorPage() {
  const isKo = useLanguage() === 'ko';
  const calculator = useCompoundCalculator(isKo);

  return (
    <div className="min-w-0 space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
          <Calculator className="h-6 w-6 text-primary-400" />
          {isKo ? '트레이딩 복리 계산기' : 'Trading Compound Calculator'}
        </h1>
        <div className="flex items-center gap-2 text-sm">
          <div className="rounded-lg border border-dark-700 bg-dark-800/70 px-3 py-2 font-mono text-dark-200">
            {calculator.scenario.winTrades}{isKo ? '승' : 'W'} / {calculator.scenario.lossTrades}
            {isKo ? '패' : 'L'}
          </div>
          <div className="rounded-lg border border-dark-700 bg-dark-800/70 px-3 py-2 font-mono text-dark-200">
            EV {calculator.evPerR >= 0 ? '+' : ''}
            {calculator.evPerR.toFixed(3)}R
          </div>
        </div>
      </div>

      <CalculatorControls
        isKo={isKo}
        capital={calculator.capital}
        trades={calculator.trades}
        risk={calculator.risk}
        rr={calculator.rr}
        winRate={calculator.winRate}
        slippage={calculator.slippage}
        setCapital={calculator.setCapital}
        setTrades={calculator.setTrades}
        setRisk={calculator.setRisk}
        setRr={calculator.setRr}
        setWinRate={calculator.setWinRate}
        setSlippage={calculator.setSlippage}
      />
      <CalculatorMetrics
        isKo={isKo}
        initialCapital={calculator.initialCapital}
        evPerR={calculator.evPerR}
        finalCapital={calculator.finalCapital}
        roi={calculator.roi}
        maxDrawdown={calculator.compound.maxDrawdown}
        worstCaseDrawdown={calculator.compound.worstCaseDrawdown}
      />
      <GrowthChart
        isKo={isKo}
        trades={calculator.trades}
        compoundBalances={calculator.compound.balances}
        simpleBalances={calculator.simpleBalances}
        chartMode={calculator.chartMode}
        setChartMode={calculator.setChartMode}
      />
      <div className="grid min-w-0 gap-4 xl:grid-cols-2">
        <EvHeatmap
          isKo={isKo}
          slippage={calculator.slippage}
          nearestWinRate={calculator.nearestWinRate}
          nearestRr={calculator.nearestRr}
        />
        <RiskTable isKo={isKo} rows={calculator.riskRows} />
      </div>
      <CheckpointTable
        isKo={isKo}
        initialCapital={calculator.initialCapital}
        rows={calculator.summaryRows}
      />
    </div>
  );
}
