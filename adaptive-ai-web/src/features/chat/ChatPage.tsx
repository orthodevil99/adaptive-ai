import React, { useEffect, useState } from 'react';
import type { MessageItem } from '../../api/types';
import { useRespond, useSession } from '../../hooks/useAdaptiveApi';
import { useAppStore } from '../../store/useAppStore';
import { computeAScore } from '../../lib/formatters';
import { MessageList } from './MessageList';
import { Composer } from './Composer';
import { InsightsPanel } from './InsightsPanel';

export const ChatPage: React.FC = () => {
  const { userId, sessionId, quickPreferences, selectedMessage, insightsOpen, selectMessageForInsights, setInsightsOpen } =
    useAppStore();
  const { data: sessionData } = useSession(sessionId, userId);
  const respondMut = useRespond();
  const [localMessages, setLocalMessages] = useState<MessageItem[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (sessionData?.messages && Array.isArray(sessionData.messages)) {
      const mapped: MessageItem[] = sessionData.messages.map((m, idx) => ({
        message_id: String(m.id || `hist_${idx}`),
        interaction_id: m.interaction_id ? String(m.interaction_id) : null,
        session_id: sessionId,
        role: m.role === 'user' ? 'user' : 'assistant',
        content: String(m.content || ''),
        created_at: String(m.created_at || new Date().toISOString()),
      }));
      setLocalMessages(mapped);
    } else {
      setLocalMessages([]);
    }
  }, [sessionData, sessionId]);

  const sendMessage = (text: string) => {
    setErrorMsg(null);
    const optimisticUser: MessageItem = {
      message_id: `local_${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, optimisticUser]);

    respondMut.mutate(
      {
        session_id: sessionId,
        user_id: userId,
        message: text,
        preferred_persona: quickPreferences.preferred_persona || undefined,
        response_length: quickPreferences.response_length || undefined,
      },
      {
        onSuccess: (res) => {
          const content =
            res.status === 'needs_clarification'
              ? res.analysis.clarification_question || 'Could you share a bit more detail so I can help?'
              : res.answer || 'No response returned.';
          const assistantMsg: MessageItem = {
            message_id: res.interaction_id || `resp_${Date.now()}`,
            interaction_id: res.interaction_id,
            session_id: res.session_id || sessionId,
            role: 'assistant',
            content,
            analysis: res.analysis,
            evaluation: res.evaluation,
            meta: res.meta,
            a_score: computeAScore(res.analysis, localMessages.length > 0),
            created_at: new Date().toISOString(),
          };
          setLocalMessages((prev) => [...prev, assistantMsg]);
          selectMessageForInsights(assistantMsg);
        },
        onError: (err) => {
          setErrorMsg(err instanceof Error ? err.message : 'Request failed. Please retry.');
        },
      }
    );
  };

  return (
    <div className="flex h-[calc(100vh-56px)] md:h-screen">
      <div className="flex flex-1 flex-col overflow-hidden">
        {errorMsg && (
          <div className="mx-4 mt-3 flex items-center justify-between rounded-xl border border-amber-400/60 bg-amber-500/10 px-4 py-2 text-xs text-amber-200 md:mx-8">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="underline">
              Dismiss
            </button>
          </div>
        )}
        <MessageList
          messages={localMessages}
          isLoading={respondMut.isPending}
          onInspect={(m) => selectMessageForInsights(m)}
          onRegenerate={(p) => sendMessage(p)}
          onQuickPrompt={(p) => sendMessage(p)}
        />
        <Composer isSending={respondMut.isPending} onSend={(t) => sendMessage(t)} />
      </div>

      {insightsOpen && selectedMessage && (
        <div className="hidden w-80 shrink-0 p-4 lg:block">
          <InsightsPanel message={selectedMessage} onClose={() => setInsightsOpen(false)} />
        </div>
      )}
    </div>
  );
};
