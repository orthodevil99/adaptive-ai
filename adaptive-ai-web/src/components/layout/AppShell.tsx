import React, { useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  Activity,
  FlaskConical,
  History,
  Menu,
  MessageSquare,
  Moon,
  Plus,
  SlidersHorizontal,
  Sparkles,
  Sun,
  X,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { useHealth } from '../../hooks/useAdaptiveApi';
import { GlassButton } from '../glass/GlassButton';

const NAV_ITEMS = [
  { to: '/', label: 'Chat Console', icon: MessageSquare },
  { to: '/playground', label: 'Analyze Playground', icon: FlaskConical },
  { to: '/sessions', label: 'Sessions', icon: History },
  { to: '/preferences', label: 'Preferences', icon: SlidersHorizontal },
  { to: '/status', label: 'System Status', icon: Activity },
];

export const AppShell: React.FC = () => {
  const { theme, toggleTheme, createNewSession, mobileNavOpen, setMobileNavOpen } = useAppStore();
  const { data: health } = useHealth();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      {/* Desktop Sidebar (Level 1 Glass) */}
      <aside className="glass hidden w-64 shrink-0 flex-col justify-between rounded-none border-y-0 border-l-0 p-4 md:flex">
        <div>
          <div className="mb-6 flex items-center gap-2.5 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#6C63FF]/20 border border-[#6C63FF]/50">
              <Sparkles className="h-5 w-5 text-[#2EC4B6]" />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight">Adaptive AI</div>
              <div className="text-[11px] opacity-65">Transparent Orchestration</div>
            </div>
          </div>

          <GlassButton onClick={() => createNewSession()} className="mb-5 w-full">
            <Plus className="h-4 w-4" /> New Session
          </GlassButton>

          <nav className="space-y-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? 'bg-[#6C63FF]/20 border-l-2 border-[#6C63FF] font-semibold'
                      : 'opacity-80 hover:bg-white/5 hover:opacity-100'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="space-y-3 border-t border-white/10 pt-4">
          <div className="flex items-center justify-between px-2 text-xs">
            <span className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${health?.status === 'healthy' ? 'bg-[#2EC4B6]' : 'bg-amber-400'}`}
              />
              {health?.status === 'healthy' ? 'API Connected' : 'Checking API'}
            </span>
            <button
              onClick={toggleTheme}
              className="rounded-lg p-1.5 hover:bg-white/10"
              title="Toggle dark/light glass theme"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
          <p className="px-2 text-[11px] leading-relaxed opacity-60">
            Messages are sent to the backend and processed by Google Gemini. No API keys are stored in the browser.
          </p>
        </div>
      </aside>

      {/* Mobile Top Bar */}
      <header className="glass flex items-center justify-between rounded-none border-x-0 border-t-0 px-4 py-3 md:hidden">
        <div className="flex items-center gap-2 font-bold">
          <Sparkles className="h-5 w-5 text-[#2EC4B6]" /> Adaptive AI
        </div>
        <div className="flex items-center gap-2">
          <button onClick={toggleTheme} className="rounded-lg p-2 hover:bg-white/10">
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button onClick={() => setMobileNavOpen(!mobileNavOpen)} className="rounded-lg p-2 hover:bg-white/10">
            {mobileNavOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {mobileNavOpen && (
        <div className="glass-overlay fixed inset-0 z-50 flex flex-col p-6 md:hidden">
          <div className="mb-6 flex items-center justify-between">
            <span className="text-lg font-bold">Adaptive AI</span>
            <button onClick={() => setMobileNavOpen(false)} className="rounded-lg p-2 hover:bg-white/10">
              <X className="h-5 w-5" />
            </button>
          </div>
          <nav className="space-y-2">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                onClick={() => setMobileNavOpen(false)}
                className="flex items-center gap-3 rounded-xl px-4 py-3 text-base font-medium hover:bg-white/10"
              >
                <Icon className="h-5 w-5" />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
};
