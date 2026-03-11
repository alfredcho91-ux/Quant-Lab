// Strategy Explainer Component
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import { getStrategyInfo } from '../api/client';
import { useBacktestParams, useLanguage } from '../store/useStore';
import { getLabels } from '../store/labels';

interface StrategyExplainerProps {
  strategyId: string;
}

export default function StrategyExplainer({ strategyId }: StrategyExplainerProps) {
  const language = useLanguage();
  const backtestParams = useBacktestParams();
  const labels = getLabels(language);
  const [expanded, setExpanded] = useState(false);

  const { data: info } = useQuery({
    queryKey: ['strategyInfo', strategyId, language, backtestParams],
    queryFn: () =>
      getStrategyInfo(strategyId, language, {
        rsi_ob: backtestParams.rsi_ob,
        sma_main_len: backtestParams.sma_main_len,
        sma1_len: backtestParams.sma1_len,
        sma2_len: backtestParams.sma2_len,
      }),
    staleTime: 60000,
  });

  if (!info) return null;

  return (
    <div className="card">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-dark-700/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary-400" />
          <span className="font-medium">{labels.expander_edu}</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-dark-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-dark-400" />
        )}
      </button>

      {expanded && (
        <div className="p-4 pt-0 space-y-4 animate-fade-in">
          {/* Concept */}
          <div className="p-3 bg-dark-700/50 rounded-lg">
            <h4 className="text-xs text-dark-400 uppercase tracking-wide mb-1">
              {labels.edu_concept}
            </h4>
            <p className="text-sm text-dark-200">{info.concept}</p>
          </div>

          {/* Rules */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-3 bg-bull/10 border border-bull/20 rounded-lg">
              <h4 className="text-xs text-bull uppercase tracking-wide mb-1">
                📈 {labels.edu_long}
              </h4>
              <p className="text-sm text-dark-200 font-mono">{info.Long}</p>
            </div>
            <div className="p-3 bg-bear/10 border border-bear/20 rounded-lg">
              <h4 className="text-xs text-bear uppercase tracking-wide mb-1">
                📉 {labels.edu_short}
              </h4>
              <p className="text-sm text-dark-200 font-mono">{info.Short}</p>
            </div>
          </div>

          {/* Best Regime */}
          <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg">
            <h4 className="text-xs text-warning uppercase tracking-wide mb-1">
              🎯 {labels.edu_regime}
            </h4>
            <p className="text-sm text-dark-200">{info.regime}</p>
          </div>

          {/* Note */}
          <p className="text-xs text-dark-500 italic">{labels.edu_note}</p>
        </div>
      )}
    </div>
  );
}
