import React from 'react';

interface GlassPanelProps {
  title: string;
  subtitle?: string;
  onClose?: () => void;
  children: React.ReactNode;
}

export const GlassPanel: React.FC<GlassPanelProps> = ({ title, subtitle, onClose, children }) => (
  <aside className="glass-elevated flex h-full flex-col overflow-hidden p-5">
    <div className="mb-4 flex items-start justify-between gap-2 border-b border-white/10 pb-3">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {subtitle && <p className="text-xs opacity-70">{subtitle}</p>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          aria-label="Close panel"
          className="rounded-lg px-2 py-1 text-xs opacity-75 hover:bg-white/10 hover:opacity-100"
        >
          Close
        </button>
      )}
    </div>
    <div className="flex-1 overflow-y-auto pr-1">{children}</div>
  </aside>
);
