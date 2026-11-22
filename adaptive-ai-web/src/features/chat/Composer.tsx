import React from 'react';
import { Send } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { GlassButton } from '../../components/glass/GlassButton';
import { PreferencePopover } from './PreferencePopover';

const MAX_LEN = Number(import.meta.env.VITE_MAX_MESSAGE_LENGTH || 4000);

interface Props {
  isSending: boolean;
  onSend: (text: string) => void;
}

export const Composer: React.FC<Props> = ({ isSending, onSend }) => {
  const { draftMessage, setDraftMessage } = useAppStore();

  const submit = () => {
    const trimmed = draftMessage.trim();
    if (!trimmed || isSending || trimmed.length > MAX_LEN) return;
    onSend(trimmed);
    setDraftMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="px-4 pb-4 pt-2 md:px-8">
      <div className="glass-elevated mx-auto flex max-w-3xl items-end gap-2 p-2.5 focus-within:ring-2 focus-within:ring-[#6C63FF]">
        <PreferencePopover />
        <textarea
          rows={1}
          value={draftMessage}
          onChange={(e) => setDraftMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Adaptive AI anything... (Enter to send, Shift+Enter for newline)"
          className="max-h-36 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none"
        />
        <span className="hidden font-mono text-[10px] opacity-50 sm:inline">
          {draftMessage.length}/{MAX_LEN}
        </span>
        <GlassButton onClick={submit} disabled={isSending || !draftMessage.trim()}>
          <Send className="h-4 w-4" />
          <span className="hidden sm:inline">Send</span>
        </GlassButton>
      </div>
    </div>
  );
};
