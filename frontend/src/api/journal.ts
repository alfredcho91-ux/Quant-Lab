// 매매 일지 API

import { api, ApiResponse } from './config';
import type { JournalEntry } from '../types';

export async function getJournal(): Promise<JournalEntry[] | null> {
  try {
    const res = await api.get<ApiResponse<JournalEntry[]>>('/journal');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function addJournalEntry(entry: Omit<JournalEntry, 'id' | 'created_at'>): Promise<JournalEntry | null> {
  try {
    const res = await api.post<{
      success: boolean;
      data: JournalEntry;
      error?: string;
    }>('/journal', entry);
    return res.data.success ? res.data.data : null;
  } catch {
    return null;
  }
}

export async function deleteJournalEntry(id: number): Promise<boolean> {
  try {
    const res = await api.delete<ApiResponse<null>>(`/journal/${id}`);
    return res.data.success;
  } catch {
    return false;
  }
}
