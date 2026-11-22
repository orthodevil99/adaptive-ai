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

  const isHealthy = Boolean(health && (health.status === 'ok' || health.status === 'healthy'));

  return (
    <div className="relative min-h-screen">
      {/* Design 3 Circuit-Board Backdrop */}
      <div className="circuit-backdrop" aria-hidden="true">
        <div className="circuit-core-glow" />
        <svg viewBox="0 0 1440 900" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="appTrace1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#2EC4B6" stopOpacity="0.65" />
              <stop offset="50%" stopColor="#6C63FF" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#2EC4B6" stopOpacity="0.15" />
            </linearGradient>
            <linearGradient id="appTrace2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#6C63FF" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#2EC4B6" stopOpacity="0.3" />
            </linearGradient>
          </defs>
          <path d="M260 0 V140 L310 190 V340 L360 390 H520" stroke="url(#appTrace1)" strokeWidth="1.4" />
          <path d="M300 0 V110 L350 160 V290 L410 350 H540" stroke="url(#appTrace1)" strokeWidth="1" />
          <path d="M260 900 V720 L320 660 V540 L380 480 H520" stroke="url(#appTrace2)" strokeWidth="1.4" />
          <path d="M580 0 V210 L620 250 V310" stroke="url(#appTrace1)" strokeWidth="1.3" />
          <path d="M720 0 V310" stroke="url(#appTrace1)" strokeWidth="1.2" />
          <path d="M860 0 V220 L820 260 V310" stroke="url(#appTrace1)" strokeWidth="1.3" />
          <path d="M600 900 V690 L640 650 V570" stroke="url(#appTrace2)" strokeWidth="1.3" />
          <path d="M840 900 V660 L800 620 V570" stroke="url(#appTrace1)" strokeWidth="1.2" />
          <path d="M1440 160 H1160 L1100 220 V360 L1020 440 H890" stroke="url(#appTrace1)" strokeWidth="1.4" />
          <path d="M1440 680 H1180 L1120 620 V530 L1050 460" stroke="url(#appTrace1)" strokeWidth="1.3" />
          <rect x="540" y="310" width="350" height="260" rx="24" stroke="url(#appTrace1)" strokeWidth="1.5" strokeOpacity="0.7" />
          <circle cx="310" cy="190" r="3.5" fill="#2EC4B6" />
          <circle cx="580" cy="210" r="3.5" fill="#2EC4B6" />
          <circle cx="860" cy="220" r="3.5" fill="#6C63FF" />
          <circle cx="1100" cy="220" r="3.5" fill="#2EC4B6" />
          <circle cx="1120" cy="620" r="3.5" fill="#6C63FF" />
          <circle cx="320" cy="660" r="3.5" fill="#2EC4B6" />
        </svg>
      </div>

      <div className="relative z-10 flex min-h-screen flex-col md:flex-row">
        {/* Desktop Sidebar (Level 1 Glass) */}
        <aside className="glass hidden w-64 shrink-0 flex-col justify-between rounded-none border-y-0 border-l-0 p-4 md:flex">
          <div>
            <div className="mb-6 flex items-center gap-2.5 px-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#6C63FF]/50 bg-[#6C63FF]/20">
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
                      isActive ? 'nav-active-glass' : 'opacity-80 hover:bg-white/5 hover:opacity-100'
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
                <span className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-[#2EC4B6]' : 'bg-amber-400'}`} />
                {isHealthy ? 'API Connected' : 'Local Demo Mode'}
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
              Circuit Glass UI connected to adaptive_ai_v3. Set VITE_API_BASE_URL in Vercel env to connect your deployed backend.
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

        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
