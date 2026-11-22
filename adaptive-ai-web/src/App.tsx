import React, { Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';
import { ChatPage } from './features/chat/ChatPage';

const PlaygroundPage = React.lazy(() =>
  import('./features/playground/PlaygroundPage').then((m) => ({ default: m.PlaygroundPage }))
);
const SessionsPage = React.lazy(() =>
  import('./features/sessions/SessionsPage').then((m) => ({ default: m.SessionsPage }))
);
const PreferencesPage = React.lazy(() =>
  import('./features/preferences/PreferencesPage').then((m) => ({ default: m.PreferencesPage }))
);
const StatusPage = React.lazy(() =>
  import('./features/status/StatusPage').then((m) => ({ default: m.StatusPage }))
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<div className="p-8 text-sm opacity-75">Loading Adaptive AI...</div>}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<ChatPage />} />
              <Route path="/playground" element={<PlaygroundPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
              <Route path="/preferences" element={<PreferencesPage />} />
              <Route path="/status" element={<StatusPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
