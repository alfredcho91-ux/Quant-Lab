/**
 * Formats a number to a fixed number of decimal places.
 * Returns '—' if the value is null or NaN.
 */
export function formatNum(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(value)) return '—';
  return value.toFixed(digits);
}
