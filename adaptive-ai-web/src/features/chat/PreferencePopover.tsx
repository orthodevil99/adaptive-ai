import React, { useState } from 'react';
import { SlidersHorizontal } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import type { PersonaType, ResponseLength } from '../../api/types';

export const PreferencePopover: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { quickPreferences, setQuickPreferences } = useAppStore();

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="glass rounded-xl p-2.5 hover:border-[#6C63FF]"
        title="Quick response preferences"
      >
        <SlidersHorizontal className="h-4 w-4" />
      </button>

      {open && (
        <div className="glass-elevated absolute bottom-12 left-0 z-30 w-64 space-y-3 p-4 text-xs">
          <div className="font-semibold">Quick Overrides</div>
          <label className="block">
            <span className="mb-1 block opacity-75">Response Length</span>
            <select
              value={quickPreferences.response_length || 'medium'}
              onChange={(e) =>
                setQuickPreferences({
                  ...quickPreferences,
                  response_length: e.target.value as ResponseLength,
                })
              }
              className="glass w-full rounded-lg px-2.5 py-1.5 outline-none"
            >
              <option value="short">Short</option>
              <option value="medium">Medium</option>
              <option value="detailed">Detailed</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block opacity-75">Preferred Persona</span>
            <select
              value={quickPreferences.preferred_persona || ''}
              onChange={(e) =>
                setQuickPreferences({
                  ...quickPreferences,
                  preferred_persona: (e.target.value || null) as PersonaType | null,
                })
              }
              className="glass w-full rounded-lg px-2.5 py-1.5 outline-none"
            >
              <option value="">Auto (Adaptive)</option>
              <option value="educational">Educational</option>
              <option value="technical">Technical</option>
              <option value="researcher">Researcher</option>
              <option value="planner">Planner</option>
              <option value="analyst">Analyst</option>
              <option value="creative">Creative</option>
              <option value="concise">Concise</option>
            </select>
          </label>
        </div>
      )}
    </div>
  );
};
