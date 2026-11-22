import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { MessageItem, PersonaType, ResponseLength } from '../api/types';

function makeId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

interface QuickPrefs {
  preferred_persona?: PersonaType | null;
  response_length?: ResponseLength | null;
}

interface AppState {
  userId: string;
  sessionId: string;
  draftMessage: string;
  quickPreferences: QuickPrefs;
  theme: 'dark' | 'light';
  selectedMessage: MessageItem | null;
  insightsOpen: boolean;
  mobileNavOpen: boolean;
  setSessionId: (id: string) => void;
  createNewSession: () => string;
  setDraftMessage: (msg: string) => void;
  setQuickPreferences: (prefs: QuickPrefs) => void;
  toggleTheme: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  selectMessageForInsights: (msg: MessageItem | null) => void;
  setInsightsOpen: (open: boolean) => void;
  setMobileNavOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      userId: makeId('user'),
      sessionId: makeId('session'),
      draftMessage: '',
      quickPreferences: { response_length: 'medium', preferred_persona: null },
      theme: 'dark',
      selectedMessage: null,
      insightsOpen: true,
      mobileNavOpen: false,

      setSessionId: (sessionId) => set({ sessionId, selectedMessage: null }),
      createNewSession: () => {
        const next = makeId('session');
        set({ sessionId: next, selectedMessage: null, draftMessage: '' });
        return next;
      },
      setDraftMessage: (draftMessage) => set({ draftMessage }),
      setQuickPreferences: (quickPreferences) => set({ quickPreferences }),
      toggleTheme: () => {
        const next = get().theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        set({ theme: next });
      },
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
      },
      selectMessageForInsights: (msg) => set({ selectedMessage: msg, insightsOpen: Boolean(msg) }),
      setInsightsOpen: (insightsOpen) => set({ insightsOpen }),
      setMobileNavOpen: (mobileNavOpen) => set({ mobileNavOpen }),
    }),
    {
      name: 'adaptive-ai-v3-client-state',
      partialize: (state) => ({
        userId: state.userId,
        sessionId: state.sessionId,
        quickPreferences: state.quickPreferences,
        theme: state.theme,
      }),
    }
  )
);
