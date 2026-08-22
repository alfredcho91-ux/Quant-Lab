import { describe, expect, it } from 'vitest';
import { calculateHoldReentry } from './holdReentry';

describe('calculateHoldReentry', () => {
  it('uses a manually supplied one-way fee instead of the leverage default', () => {
    const result = calculateHoldReentry({
      direction: 'long',
      entryPrice: 100,
      currentPrice: 99,
      reentryPrice: 98,
      targetPrice: 102,
      marginUsd: 100,
      leverage: 10,
      feePercent: 0.06,
    });

    expect(result.effectiveFeePercent).toBe(0.06);
    expect(result.incrementalFees).toBeCloseTo(1.2064898, 6);
  });

  it('calculates the supplied long hold-versus-reentry example', () => {
    const result = calculateHoldReentry({
      direction: 'long',
      entryPrice: 64_000,
      currentPrice: 63_600,
      reentryPrice: 63_000,
      targetPrice: 65_000,
      marginUsd: 64_000,
      leverage: 1,
    });

    expect(result.currentPnlPercent).toBeCloseTo(-0.625, 5);
    expect(result.holdingPnl).toBe(1_000);
    expect(result.realizedPnl).toBe(-400);
    expect(result.reentryPnl).toBeCloseTo(2_031.74603, 5);
    expect(result.reentryFinalPnl).toBeCloseTo(1_631.74603, 5);
    expect(result.grossReentryAdvantage).toBeCloseTo(631.74603, 5);
    expect(result.positionQuantity).toBe(1);
    expect(result.reentryQuantity).toBeCloseTo(1.015873, 5);
    expect(result.effectiveFeePercent).toBe(0.04);
    expect(result.incrementalFees).toBeCloseTo(51.452698, 5);
    expect(result.netReentryAdvantage).toBeCloseTo(580.293333, 5);
  });

  it('uses the correct sign convention for a short position', () => {
    const result = calculateHoldReentry({
      direction: 'short',
      entryPrice: 100,
      currentPrice: 101,
      reentryPrice: 102,
      targetPrice: 98,
      marginUsd: 100,
      leverage: 1,
    });

    expect(result.realizedPnl).toBe(-1);
    expect(result.reentryPnl).toBeCloseTo(3.921568, 5);
    expect(result.reentryFinalPnl).toBeCloseTo(2.921568, 5);
    expect(result.holdingPnl).toBe(2);
    expect(result.netReentryAdvantage).toBeCloseTo(0.841937, 5);
  });

  it('scales position P&L and the margin-basis fee rate with leverage', () => {
    const result = calculateHoldReentry({
      direction: 'long',
      entryPrice: 100,
      currentPrice: 99,
      reentryPrice: 98,
      targetPrice: 102,
      marginUsd: 100,
      leverage: 10,
    });

    expect(result.positionQuantity).toBe(10);
    expect(result.reentryQuantity).toBeCloseTo(10.204082, 5);
    expect(result.holdingPnl).toBe(20);
    expect(result.holdingPnlPercent).toBe(20);
    expect(result.effectiveFeePercent).toBeCloseTo(0.4, 5);
  });

  it('uses the selected direction instead of inferring it from target price', () => {
    const result = calculateHoldReentry({
      direction: 'short',
      entryPrice: 100,
      currentPrice: 99,
      reentryPrice: 98,
      targetPrice: 102,
      marginUsd: 100,
      leverage: 1,
    });

    expect(result.direction).toBe('short');
    expect(result.currentPnl).toBe(1);
    expect(result.holdingPnl).toBe(-2);
  });
});
