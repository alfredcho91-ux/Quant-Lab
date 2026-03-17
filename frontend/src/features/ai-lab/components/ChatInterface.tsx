import { useEffect, useRef, useState, memo } from 'react';
import { Bot, Send, User } from 'lucide-react';
import type { Message } from '../hooks/useAIResearch';

interface ChatInterfaceProps {
  messages: Message[];
  isTyping: boolean;
  isKo: boolean;
  onSend: (text: string) => void | Promise<void>;
}

// [Optimization] MessageBubble 컴포넌트 분리 및 Memoization
const MessageBubble = memo(({ message }: { message: Message }) => {
  const isUser = message.role === 'user';
  return (
    <div
      className={`flex items-start gap-2 ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center shrink-0">
          <Bot className="w-3.5 h-3.5" />
        </div>
      )}
      <div
        className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
          isUser
            ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-100'
            : 'bg-dark-700/80 border border-dark-600 text-dark-100'
        }`}
      >
        {message.content}
      </div>
      {isUser && (
        <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center shrink-0">
          <User className="w-3.5 h-3.5" />
        </div>
      )}
    </div>
  );
});

export default function ChatInterface({
  messages,
  isTyping,
  isKo,
  onSend,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const submit = async (textOverride?: string) => {
    const text = textOverride ?? input.trim();
    if (!text) return;
    if (!textOverride) setInput('');
    await onSend(text);
  };

  // [UX] 추천 질문 목록
  const suggestions = isKo
    ? ['방금 전략 파라미터 최적화해줘']
    : ['Optimize the latest strategy params'];

  return (
    <div className="card h-full p-0 overflow-hidden flex flex-col">
      <div className="px-4 py-3 border-b border-dark-700 bg-dark-800/60">
        <h2 className="text-sm font-semibold text-white">{isKo ? 'AI 채팅' : 'AI Chat'}</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isTyping && (
          <div className="flex items-center gap-2 text-dark-400 text-xs px-1">
            <Bot className="w-3.5 h-3.5" />
            <span>{isKo ? 'AI가 답변 작성 중...' : 'AI is typing...'}</span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-dark-700 p-3 bg-dark-800/50">
        {/* [UX] 추천 질문 칩 */}
        <div className="flex gap-2 mb-2 overflow-x-auto no-scrollbar pb-1">
          {suggestions.map((text) => (
            <button
              key={text}
              onClick={() => void submit(text)}
              className="text-xs px-2.5 py-1.5 rounded-full bg-dark-700 text-dark-300 hover:bg-dark-600 hover:text-dark-100 transition-colors whitespace-nowrap border border-dark-600"
            >
              {text}
            </button>
          ))}
        </div>

        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                void submit();
              }
            }}
            placeholder={
              isKo ? '전략을 자연어로 입력...' : 'Describe your strategy in natural language...'
            }
            className="flex-1 min-h-[44px] max-h-32 resize-none bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all outline-none placeholder:text-dark-500"
          />
          <button
            onClick={() => void submit()}
            className="btn btn-primary h-[44px] px-3 flex items-center gap-1"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
