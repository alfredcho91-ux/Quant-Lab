// Parameters Panel Component
import { useState } from 'react';
import { ChevronDown, ChevronUp, Save, RefreshCw } from 'lucide-react';
import {
  useBacktestParams,
  useLanguage,
  useResetBacktestParams,
  useUpdateBacktestParams,
} from '../store/useStore';
import { getLabels } from '../store/labels';

interface ParamsPanelProps {
  onSavePreset?: () => void;
  onLoadPreset?: () => void;
}

export default function ParamsPanel({ onSavePreset }: ParamsPanelProps) {
  const language = useLanguage();
  const backtestParams = useBacktestParams();
  const updateBacktestParams = useUpdateBacktestParams();
  const resetBacktestParams = useResetBacktestParams();
  const labels = getLabels(language);
  const [expanded, setExpanded] = useState(true);

  const NumberInput = ({
    label,
    value,
    onChange,
    min,
    max,
    step = 1,
  }: {
    label: string;
    value: number;
    onChange: (v: number) => void;
    min?: number;
    max?: number;
    step?: number;
  }) => (
    <div className="space-y-1">
      <label className="text-xs text-dark-400">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full"
      />
    </div>
  );

  return (
    <div className="card">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-dark-700/50 transition-colors"
      >
        <span className="text-lg font-semibold">{labels.params}</span>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-dark-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-dark-400" />
        )}
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4 pt-0 space-y-6">
          {/* Trading Parameters */}
          <div>
            <h4 className="text-sm font-medium text-primary-400 mb-3">📊 Trading</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <NumberInput
                label={labels.tp}
                value={backtestParams.tp_pct}
                onChange={(v) => updateBacktestParams({ tp_pct: v })}
                min={0.1}
                max={100}
                step={0.1}
              />
              <NumberInput
                label={labels.sl}
                value={backtestParams.sl_pct}
                onChange={(v) => updateBacktestParams({ sl_pct: v })}
                min={0.1}
                max={50}
                step={0.1}
              />
              <NumberInput
                label={labels.maxbars}
                value={backtestParams.max_bars}
                onChange={(v) => updateBacktestParams({ max_bars: v })}
                min={1}
                max={240}
              />
              <div className="space-y-1">
                <label className="text-xs text-dark-400">{labels.leverage}</label>
                <select
                  value={backtestParams.leverage}
                  onChange={(e) => updateBacktestParams({ leverage: Number(e.target.value) })}
                  className="w-full"
                >
                  {[1, 5, 10, 20, 30, 50].map((v) => (
                    <option key={v} value={v}>
                      {v}x
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Trend Parameters */}
          <div>
            <h4 className="text-sm font-medium text-primary-400 mb-3">📈 Trend</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <NumberInput
                label={labels.sma_main_len}
                value={backtestParams.sma_main_len}
                onChange={(v) => updateBacktestParams({ sma_main_len: v })}
                min={20}
                max={400}
              />
              <NumberInput
                label={labels.sma1_len}
                value={backtestParams.sma1_len}
                onChange={(v) => updateBacktestParams({ sma1_len: v })}
                min={5}
                max={200}
              />
              <NumberInput
                label={labels.sma2_len}
                value={backtestParams.sma2_len}
                onChange={(v) => updateBacktestParams({ sma2_len: v })}
                min={5}
                max={400}
              />
              <NumberInput
                label={labels.adx_thr}
                value={backtestParams.adx_thr}
                onChange={(v) => updateBacktestParams({ adx_thr: v })}
                min={5}
                max={60}
              />
              <NumberInput
                label={labels.donch}
                value={backtestParams.donch}
                onChange={(v) => updateBacktestParams({ donch: v })}
                min={5}
                max={100}
              />
            </div>
          </div>

          {/* Momentum Parameters */}
          <div>
            <h4 className="text-sm font-medium text-primary-400 mb-3">⚡ Momentum</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <NumberInput
                label={labels.rsi14_ob}
                value={backtestParams.rsi_ob}
                onChange={(v) => updateBacktestParams({ rsi_ob: v })}
                min={50}
                max={95}
              />
              <NumberInput
                label="MACD Fast"
                value={backtestParams.macd_fast}
                onChange={(v) => updateBacktestParams({ macd_fast: v })}
                min={1}
                max={50}
              />
              <NumberInput
                label="MACD Slow"
                value={backtestParams.macd_slow}
                onChange={(v) => updateBacktestParams({ macd_slow: v })}
                min={2}
                max={100}
              />
              <NumberInput
                label="MACD Signal"
                value={backtestParams.macd_signal}
                onChange={(v) => updateBacktestParams({ macd_signal: v })}
                min={1}
                max={50}
              />
            </div>
          </div>

          {/* Volatility Parameters */}
          <div>
            <h4 className="text-sm font-medium text-primary-400 mb-3">🌪 Volatility</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <NumberInput
                label="BB Length"
                value={backtestParams.bb_length}
                onChange={(v) => updateBacktestParams({ bb_length: v })}
                min={5}
                max={100}
              />
              <NumberInput
                label="BB Std Mult"
                value={backtestParams.bb_std_mult}
                onChange={(v) => updateBacktestParams({ bb_std_mult: v })}
                min={0.5}
                max={5}
                step={0.1}
              />
              <NumberInput
                label="ATR Length"
                value={backtestParams.atr_length}
                onChange={(v) => updateBacktestParams({ atr_length: v })}
                min={5}
                max={100}
              />
              <NumberInput
                label="KC Mult"
                value={backtestParams.kc_mult}
                onChange={(v) => updateBacktestParams({ kc_mult: v })}
                min={0.5}
                max={5}
                step={0.1}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-4 border-t border-dark-700">
            <button
              onClick={resetBacktestParams}
              className="btn btn-secondary flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Reset
            </button>
            {onSavePreset && (
              <button
                onClick={onSavePreset}
                className="btn btn-primary flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Preset
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
