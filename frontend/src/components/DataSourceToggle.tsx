// Data Source Toggle Component (API/CSV)
import { useStore } from '../store/useStore';
import { getLabels } from '../store/labels';

interface DataSourceToggleProps {
  className?: string;
  showLabel?: boolean;
}

export default function DataSourceToggle({ className = '', showLabel = true }: DataSourceToggleProps) {
  const { language, backtestParams, updateBacktestParams } = useStore();
  const labels = getLabels(language);

  return (
    <div className={`space-y-2 ${className}`}>
      {showLabel && (
        <label className="text-xs text-dark-400 uppercase">{labels.data_src}</label>
      )}
      <div className="flex gap-2">
        <button
          onClick={() => updateBacktestParams({ use_csv: false })}
          className={`flex-1 py-2 px-3 rounded-lg text-sm transition-all ${
            !backtestParams.use_csv
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
          }`}
        >
          {labels.data_api}
        </button>
        <button
          onClick={() => updateBacktestParams({ use_csv: true })}
          className={`flex-1 py-2 px-3 rounded-lg text-sm transition-all ${
            backtestParams.use_csv
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
          }`}
        >
          {labels.data_csv}
        </button>
      </div>
    </div>
  );
}
