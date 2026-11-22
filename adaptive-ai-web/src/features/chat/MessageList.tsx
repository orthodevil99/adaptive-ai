import React from 'react';
import type { MessageItem } from '../../api/types';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: MessageItem[];
  isLoading: boolean;
  onInspect: (msg: MessageItem) => void;
  onRegenerate: (prompt: string) => void;
  onQuickPrompt: (prompt: string) => void;
}

const SAMPLE_PROMPTS = [
  'Explain how neural networks learn step by step',
  'Write a typed FastAPI endpoint with Pydantic validation',
  'Plan a 2-week MVP roadmap for an AI SaaS product',
  'Compare trade-offs between RAG and fine-tuning',
];

export const MessageList: React.FC<Props> = ({
  messages,
  isLoading,
  onInspect,
  onRegenerate,
  onQuickPrompt,
}) => {
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
        <h1 className="mb-2 text-2xl font-bold">See How Every Answer Is Orchestrated</h1>
        <p className="mb-6 max-w-lg text-sm opacity-75">
          Ask any question to inspect detected intent, complexity, persona, response strategy, A-score breakdown, and 5-dimension evaluation in real time.
        </p>
        <div className="grid w-full max-w-2xl gap-2.5 sm:grid-cols-2">
          {SAMPLE_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => onQuickPrompt(p)}
              className="glass rounded-xl p-3.5 text-left text-xs transition hover:border-[#6C63FF]"
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 overflow-y-auto px-4 py-6 md:px-8">
      {messages.map((msg, i) => {
        const prevUser = i > 0 && messages[i - 1].role === 'user' ? messages[i - 1].content : '';
        return (
          <MessageBubble
            key={msg.message_id}
            message={msg}
            onInspect={onInspect}
            onRegenerate={() => prevUser && onRegenerate(prevUser)}
          />
        );
      })}
      {isLoading && (
        <div className="glass max-w-md animate-pulse px-4 py-3 text-sm opacity-80">
          Analyzing intent, selecting persona, and evaluating response...
        </div>
      )}
    </div>
  );
};
