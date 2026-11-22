import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, MessageSquare } from 'lucide-react';
import { useDeleteSession, useUserSessions } from '../../hooks/useAdaptiveApi';
import { useAppStore } from '../../store/useAppStore';
import { GlassCard } from '../../components/glass/GlassCard';
import { GlassButton } from '../../components/glass/GlassButton';

export const SessionsPage: React.FC = () => {
  const { userId, sessionId, setSessionId, createNewSession } = useAppStore();
  const { data, isLoading } = useUserSessions(userId);
  const deleteMut = useDeleteSession(userId);
  const navigate = useNavigate();
  const sessions = data?.sessions || [];

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6 md:p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Sessions</h1>
          <p className="text-sm opacity-75">User ID: <code>{userId}</code></p>
        </div>
        <GlassButton
          onClick={() => {
            createNewSession();
            navigate('/');
          }}
        >
          New Session
        </GlassButton>
      </div>

      {isLoading ? (
        <GlassCard className="p-6 text-sm opacity-70">Loading sessions...</GlassCard>
      ) : sessions.length === 0 ? (
        <GlassCard className="p-6 text-sm opacity-70">No saved sessions yet. Send a message in Chat Console to create one.</GlassCard>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <GlassCard key={s.session_id} className="flex items-center justify-between gap-4 p-4">
              <button
                onClick={() => {
                  setSessionId(s.session_id);
                  navigate('/');
                }}
                className="flex flex-1 items-center gap-3 text-left"
              >
                <MessageSquare className="h-4 w-4 text-[#2EC4B6]" />
                <div>
                  <div className="font-semibold">
                    {s.title || s.session_id}{' '}
                    {s.session_id === sessionId && <span className="text-xs text-[#2EC4B6]">(Active)</span>}
                  </div>
                  <div className="text-xs opacity-65">{s.message_count ?? 0} messages</div>
                </div>
              </button>
              <button
                onClick={() => deleteMut.mutate(s.session_id)}
                aria-label="Delete session"
                className="rounded-lg p-2 opacity-70 hover:bg-white/10 hover:opacity-100"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
};
