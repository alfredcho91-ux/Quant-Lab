// 주간 패턴 분석 - 가격 입력 패널 컴포넌트

import { RefreshCw } from 'lucide-react';
import type { WeeklyPatternParams } from '../../types';

interface PriceInputPanelProps {
  mondayOpen: number | '';
  tuesdayClose: number | '';
  params: WeeklyPatternParams;
  isLoadingOHLCV: boolean;
  isKo: boolean;
  onTuesdayCloseChange: (value: number | '') => void;
}

export function PriceInputPanel({
  mondayOpen,
  tuesdayClose,
  params,
  isLoadingOHLCV,
  isKo,
  onTuesdayCloseChange,
}: PriceInputPanelProps) {
  return (
    <div className="md:col-span-2">
      <label className="block text-sm text-dark-400 mb-2">
        {isKo ? '가격 입력 (하락/상승 자동 판단 및 임계값 계산)' : 'Price Input (Auto-detect Direction & Calculate Threshold)'}
      </label>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-dark-500 mb-1">
            {isKo ? '월요일 시가 (자동 로드)' : 'Monday Open (Auto-loaded)'}
          </label>
          <div className="relative">
            <input
              type="number"
              step="0.01"
              value={mondayOpen}
              readOnly
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-300 cursor-not-allowed"
            />
            {isLoadingOHLCV && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <RefreshCw className="w-4 h-4 animate-spin text-dark-400" />
              </div>
            )}
          </div>
          <p className="text-xs text-dark-500 mt-1">
            {isKo 
              ? 'API에서 최근 월요일 시가를 자동으로 불러옵니다'
              : 'Automatically loaded from API (latest Monday open)'}
          </p>
        </div>
        <div>
          <label className="block text-xs text-dark-500 mb-1">
            {isKo ? '화요일 종가 (입력 시 하락/상승 자동 판단 및 임계값 계산)' : 'Tuesday Close (Auto-detect direction & calculate threshold)'}
          </label>
          <input
            type="number"
            step="0.01"
            value={tuesdayClose}
            onChange={(e) => {
              const value = e.target.value === '' ? '' : parseFloat(e.target.value);
              onTuesdayCloseChange(value);
            }}
            placeholder={isKo ? '예: 47500' : 'e.g., 47500'}
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
          />
          <p className="text-xs text-dark-500 mt-1">
            {isKo 
              ? '화요일 종가를 입력하면 하락/상승이 자동으로 판단되고 임계값이 계산됩니다'
              : 'Enter Tuesday close price to auto-detect direction and calculate threshold'}
          </p>
        </div>
      </div>
      {mondayOpen && tuesdayClose && typeof mondayOpen === 'number' && typeof tuesdayClose === 'number' && mondayOpen > 0 && (
        <div className="mt-2 p-2 bg-dark-800 rounded-lg">
          <div className="text-xs text-dark-400 mb-1">
            {isKo ? '계산된 임계값 (자동 판단)' : 'Calculated Threshold (Auto-detected)'}
          </div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-sm font-semibold ${
              tuesdayClose < mondayOpen ? 'text-red-400' : 'text-emerald-400'
            }`}>
              {tuesdayClose < mondayOpen 
                ? (isKo ? '📉 하락' : '📉 Drop')
                : (isKo ? '📈 상승' : '📈 Rise')}
            </span>
            <span className="text-lg font-bold text-dark-300">
              {tuesdayClose < mondayOpen
                ? (params.deep_drop_threshold * 100).toFixed(2)
                : (params.deep_rise_threshold * 100).toFixed(2)}%
            </span>
          </div>
          <div className="text-xs text-dark-500 mt-1">
            {isKo 
              ? `(${mondayOpen} → ${tuesdayClose})`
              : `(${mondayOpen} → ${tuesdayClose})`}
          </div>
        </div>
      )}
      <p className="text-xs text-dark-500 mt-2">
        {isKo
          ? '월요일 시가와 화요일 종가를 입력하면 하락/상승이 자동으로 판단되고 임계값이 계산됩니다'
          : 'Enter Monday open and Tuesday close prices to auto-detect direction and calculate threshold'}
      </p>
    </div>
  );
}
