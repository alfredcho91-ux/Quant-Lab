/**
 * Formats a number to a fixed number of decimal places.
 * Returns '—' if the value is null or NaN.
 */
export function formatNum(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return value.toFixed(Math.min(2, Math.max(0, digits)));
}
