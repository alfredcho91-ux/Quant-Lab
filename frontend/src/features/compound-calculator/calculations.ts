import type { GrowthResult, RiskRow, SummaryRow, Tone, TradeOutcome, TradeScenario } from './types';

export const HEATMAP_WIN_RATES = [30, 35, 40, 45, 50, 55, 60, 65, 70];
export const HEATMAP_RR_VALUES = [0.5, 1, 1.5, 2, 2.5, 3];

export const metricToneClass: Record<Tone, string> = {
  positive: 'text-bull',
  negative: 'text-bear',
  warning: 'text-warning',
  neutral: 'text-white',
};

const numberFormatter = new Intl.NumberFormat('ko-KR');

export function formatCompactWon(value: number) {
  if (!Number.isFinite(value)) return '-';
  const absValue = Math.abs(value);

  if (absValue >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(2)}억`;
  }
  if (absValue >= 10_000) {
    return `${numberFormatter.format(Math.round(value / 10_000))}만`;
  }
  return numberFormatter.format(Math.round(value));
}

export function formatPercent(value: number) {
  if (!Number.isFinite(value)) return '-';
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

export function calculateEvPerR(winRate: number, rrRatio: number, slippage: number) {
  const winProbability = winRate / 100;
  return winProbability * rrRatio - (1 - winProbability) * (1 + slippage / 100);
}

export function buildTradeScenario(trades: number, winRate: number): TradeScenario {
  const totalTrades = Math.max(0, Math.floor(trades));
  const winTrades = Math.min(totalTrades, Math.max(0, Math.round(totalTrades * (winRate / 100))));
  const outcomes: TradeOutcome[] = [
    ...Array<TradeOutcome>(winTrades).fill('win'),
    ...Array<TradeOutcome>(totalTrades - winTrades).fill('loss'),
  ];

  // A stable shuffle gives the same inputs the same representative trade path.
  let seed = (totalTrades * 1_103_515_245 + winTrades * 12_345 + 1) >>> 0;
  for (let index = outcomes.length - 1; index > 0; index -= 1) {
    seed = (seed * 1_664_525 + 1_013_904_223) >>> 0;
    const swapIndex = seed % (index + 1);
    [outcomes[index], outcomes[swapIndex]] = [outcomes[swapIndex], outcomes[index]];
  }

  return { outcomes, winTrades, lossTrades: totalTrades - winTrades };
}

function calculateDrawdown(balances: number[]) {
  let peak = balances[0] ?? 0;
  let maxDrawdown = 0;

  for (const balance of balances) {
    peak = Math.max(peak, balance);
    maxDrawdown = Math.max(maxDrawdown, peak > 0 ? ((peak - balance) / peak) * 100 : 0);
  }

  return maxDrawdown;
}

function buildBalances(
  initialCapital: number,
  outcomes: TradeOutcome[],
  getChange: (outcome: TradeOutcome) => number,
  compound: boolean
) {
  let balance = initialCapital;
  const balances = [initialCapital];

  for (const outcome of outcomes) {
    balance = compound ? balance * getChange(outcome) : balance + getChange(outcome);
    balances.push(Math.max(balance, 0));
  }

  return balances;
}

export function buildCompoundGrowth(
  initialCapital: number,
  riskPct: number,
  rrRatio: number,
  slippage: number,
  scenario: TradeScenario
): GrowthResult {
  const winMultiplier = 1 + (riskPct / 100) * rrRatio;
  const lossMultiplier = Math.max(0, 1 - (riskPct / 100) * (1 + slippage / 100));
  const multiplierFor = (outcome: TradeOutcome) =>
    outcome === 'win' ? winMultiplier : lossMultiplier;
  const balances = buildBalances(initialCapital, scenario.outcomes, multiplierFor, true);
  const worstCaseBalances = buildBalances(
    initialCapital,
    [...Array<TradeOutcome>(scenario.lossTrades).fill('loss'), ...Array<TradeOutcome>(scenario.winTrades).fill('win')],
    multiplierFor,
    true
  );

  return {
    balances,
    maxDrawdown: calculateDrawdown(balances),
    worstCaseDrawdown: calculateDrawdown(worstCaseBalances),
  };
}

export function buildSimpleGrowth(
  initialCapital: number,
  riskPct: number,
  rrRatio: number,
  slippage: number,
  scenario: TradeScenario
) {
  const tradeRisk = initialCapital * (riskPct / 100);
  const winAmount = tradeRisk * rrRatio;
  const lossAmount = tradeRisk * (1 + slippage / 100);
  return buildBalances(
    initialCapital,
    scenario.outcomes,
    (outcome) => (outcome === 'win' ? winAmount : -lossAmount),
    false
  );
}

export function getNearest(values: number[], target: number) {
  return values.reduce((best, current) =>
    Math.abs(current - target) < Math.abs(best - target) ? current : best
  );
}

export function buildSummaryRows(
  initialCapital: number,
  trades: number,
  compoundBalances: number[],
  simpleBalances: number[]
): SummaryRow[] {
  const checkpoints = Array.from(
    new Set([
      0,
      Math.floor(trades * 0.1),
      Math.floor(trades * 0.25),
      Math.floor(trades * 0.5),
      Math.floor(trades * 0.75),
      trades,
    ])
  );

  return checkpoints.map((trade) => {
    const compoundCapital = compoundBalances[trade] ?? initialCapital;
    const simpleCapital = simpleBalances[trade] ?? initialCapital;
    return {
      trade,
      compoundCapital,
      compoundRoi: initialCapital > 0 ? (compoundCapital / initialCapital - 1) * 100 : 0,
      simpleCapital,
      simpleRoi: initialCapital > 0 ? (simpleCapital / initialCapital - 1) * 100 : 0,
    };
  });
}

export function buildRiskRows(
  trades: number,
  winRate: number,
  risk: number,
  slippage: number,
  isKo: boolean
): RiskRow[] {
  const lossProbability = 1 - winRate / 100;
  const lossFraction = (risk / 100) * (1 + slippage / 100);

  const probabilityOfStreak = (streak: number) => {
    if (streak > trades || lossProbability <= 0) return 0;
    if (lossProbability >= 1) return 100;

    let states: number[] = Array.from({ length: streak }, (_, index) => (index === 0 ? 1 : 0));
    for (let trade = 0; trade < trades; trade += 1) {
      const nextStates: number[] = Array.from({ length: streak }, () => 0);
      const activeProbability = states.reduce((sum, probability) => sum + probability, 0);
      nextStates[0] = activeProbability * (1 - lossProbability);
      for (let losses = 0; losses < streak - 1; losses += 1) {
        nextStates[losses + 1] += states[losses] * lossProbability;
      }
      states = nextStates;
    }

    return (1 - states.reduce((sum, probability) => sum + probability, 0)) * 100;
  };

  return Array.from({ length: 8 }, (_, index) => {
    const streak = index + 3;
    const probability = probabilityOfStreak(streak);
    const capitalLoss = (1 - Math.pow(1 - lossFraction, streak)) * 100;
    const tone: Tone = capitalLoss < 10 ? 'positive' : capitalLoss < 20 ? 'warning' : 'negative';
    return {
      streak,
      probability,
      capitalLoss,
      tone,
      label:
        tone === 'positive'
          ? isKo
            ? '낮음'
            : 'Low'
          : tone === 'warning'
            ? isKo
              ? '주의'
              : 'Watch'
            : isKo
              ? '위험'
              : 'High',
    };
  });
}
