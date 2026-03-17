import { Check, Copy, Sparkles } from 'lucide-react';
import type { BacktestParams } from '../../../types';

interface StrategyDraftPreviewProps {
  draft: BacktestParams | null;
  copied: boolean;
  isKo: boolean;
  onCopy: () => void;
}

export default function StrategyDraftPreview({
  draft,
  copied,
  isKo,
  onCopy,
}: StrategyDraftPreviewProps) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          {isKo ? '실행 파라미터 JSON (BacktestParams)' : 'Executable JSON (BacktestParams)'}
        </h3>
        <button
          onClick={onCopy}
          disabled={!draft}
          className="text-xs px-2 py-1 rounded bg-dark-700 hover:bg-dark-600 disabled:opacity-40 flex items-center gap-1"
        >
          {copied ? <Check className="w-3 h-3 text-primary-400" /> : <Copy className="w-3 h-3" />}
          {isKo ? '복사' : 'Copy'}
        </button>
      </div>
      <pre className="bg-dark-900 border border-dark-700 rounded-lg p-3 text-[11px] leading-relaxed overflow-auto max-h-[520px] text-dark-200">
        {draft
          ? JSON.stringify(draft, null, 2)
          : isKo
            ? '아직 생성된 실행 파라미터가 없습니다. 좌측에서 프롬프트를 입력하고 "전략 초안 생성"을 눌러주세요.'
            : 'No executable params generated yet. Enter a prompt and click "Generate Draft".'}
      </pre>
    </div>
  );
}
