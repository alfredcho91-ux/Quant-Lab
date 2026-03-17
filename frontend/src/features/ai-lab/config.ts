export type LlmProvider = 'gemini';

export const AI_CHAT_CONFIG_KEY = 'quant-master-ai-chat-config-v1';

export const DEFAULT_MODEL_BY_PROVIDER: Record<LlmProvider, string> = {
  gemini: 'gemini-3-flash-preview',
};

const DEPRECATED_GEMINI_MODELS = new Set([
  'gemini-pro',
  'gemini-1.5-pro',
  'gemini-2.5-flash',
  'gemini-3-flash',
  'gemini-3.0-flash',
  'gemini-3-flash-latest',
  'gemini-3.0-pro-exp',
  'gemini-3.0-pro-preview',
  'gemini-3.0-pro-preivew',
  'gemini-3-pro-preview',
  'gemini-2.0-pro-exp-02-05',
]);

export function isSupportedLlmProvider(value: unknown): value is LlmProvider {
  return value === 'gemini';
}

export function normalizePreferredModel(model: string | undefined | null): string {
  const trimmed = (model || '').trim();
  if (!trimmed || DEPRECATED_GEMINI_MODELS.has(trimmed)) {
    return DEFAULT_MODEL_BY_PROVIDER.gemini;
  }
  return trimmed;
}

export function isDefaultProviderModel(model: string): boolean {
  return model === DEFAULT_MODEL_BY_PROVIDER.gemini;
}
