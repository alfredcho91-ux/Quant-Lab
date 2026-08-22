import type { JournalEntry } from '../../types';

export function isClosedPosition(entry: JournalEntry): boolean {
  return entry.source === 'deepcoin_position';
}

export function isOngoingFill(entry: JournalEntry): boolean {
  return entry.source === 'deepcoin' && entry.exit_price == null && entry.realized_pnl == null;
}
