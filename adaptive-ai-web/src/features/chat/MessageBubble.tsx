import React, { Suspense } from 'react';
import type { MessageItem } from '../../api/types';
import { GlassCard } from '../../components/glass/GlassCard';
import { InsightChips } from './InsightChips';
import { FeedbackBar } from './FeedbackBar';

const ReactMarkdown = React.lazy(() => import('react-markdown'));

interface Props {
  message: MessageItem;
  onInspect: (msg: MessageItem) => void;
  onRegenerate: () => void;
}

export const MessageBubble: React.FC<Props> = React.memo(({ message, onInspect, onRegenerate }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <GlassCard
        level={isUser ? 'user' : 'surface'}
        className={`max-w-3xl px-4 py-3.5 ${isUser ? 'w-fit' : 'w-full'}`}
      >
        <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wider opacity-60">
          <span>{isUser ? 'You' : 'Adaptive AI'}</span>
          {message.meta?.latency_ms && <span className="font-mono">{message.meta.latency_ms} ms</span>}
        </div>

        <div className="prose prose-invert max-w-none text-sm leading-relaxed">
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <Suspense fallback={<p>{message.content}</p>}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </Suspense>
          )}
        </div>

        {!isUser && (
          <>
            <InsightChips message={message} onInspect={() => onInspect(message)} />
            <FeedbackBar message={message} onRegenerate={onRegenerate} />
          </>
        )}
      </GlassCard>
    </div>
  );
});
