import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { runHybridBacktest, runHybridLiveMode } from '../../../api/client';
import {
  useSelectedCoin,
  useSelectedInterval,
  useSetSelectedCoin,
  useSetSelectedInterval,
} from '../../../store/useStore';
import type { HybridBacktestParams } from '../../../types';

export const useHybridAnalysis = () => {
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const setSelectedCoin = useSetSelectedCoin();
  const setSelectedInterval = useSetSelectedInterval();

  const [backtestParams, setBacktestParams] = useState<Omit<HybridBacktestParams, 'coin' | 'interval'>>({
    strategy: 'SMA_ADX_Strong',
    tp: 2.0,
    sl: 1.0,
    max_hold: 5,
  });

  const backtestMutation = useMutation({
    mutationFn: runHybridBacktest,
  });

  const liveModeMutation = useMutation({
    mutationFn: runHybridLiveMode,
  });

  const handleRunBacktest = () => {
    backtestMutation.mutate({
      coin: selectedCoin,
      interval: selectedInterval,
      ...backtestParams,
    });
  };

  const handleRunLiveMode = () => {
    liveModeMutation.mutate({
      coin: selectedCoin,
      interval: selectedInterval,
    });
  };

  const backtestResult = backtestMutation.data;
  const liveModeResult = liveModeMutation.data;
  const isLoading = backtestMutation.isPending || liveModeMutation.isPending;

  return {
    selectedCoin,
    selectedInterval,
    setSelectedCoin,
    setSelectedInterval,
    backtestParams,
    setBacktestParams,
    handleRunBacktest,
    handleRunLiveMode,
    backtestResult,
    liveModeResult,
    isLoading,
    backtestMutation,
    liveModeMutation,
  };
};
