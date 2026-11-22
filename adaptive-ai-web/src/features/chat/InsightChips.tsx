import React from 'react';
import { BarChart3, BookOpen, ClipboardList, Code2, Compass, Info, Search, Sparkles } from 'lucide-react';
import type { MessageItem } from '../../api/types';
import { Chip } from '../../components/glass/Chip';
import { formatLabel } from '../../lib/formatters';

function getPersonaIcon(persona?: string) {
  const p = (persona || '').toLowerCase();
  if (p.includes('educat') || p.includes('teach')) return <BookOpen className="h-3.5 w-3.5 text-[#2EC4B6]" />;
  if (p.includes('tech') || p.includes('dev')) return <Code2 className="h-3.5 w-3.5 text-[#2EC4B6]" />;
  if (p.includes('research')) return <Search className="h-3.5 w-3.5 text-[#2EC4B6]" />;
  if (p.includes('plan')) return <ClipboardList className="h-3.5 w-3.5 text-[#2EC4B6]" />;
  if (p.includes('analy')) return <BarChart3 className="h-3.5 w-3.5 text-[#2EC4B6]" />;
  return <Sparkles className="h-3.5 w-3.5 text-[#2EC4B6]" />;
}

interface Props {
  message: MessageItem;
  onInspect: () => void;
}

export const InsightChips: React.FC<Props> = ({ message, onInspect }) => {
  const analysis = message.analysis;
  const bars = analysis?.complexity === 'high' ? 3 : analysis?.complexity === 'medium' ? 2 : 1;

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <Chip onClick={onInspect}>
        <Compass className="h-3.5 w-3.5 text-[#6C63FF]" />
        <span>{formatLabel(analysis?.task_type)}</span>
      </Chip>

      <Chip onClick={onInspect}>
        <span className="flex items-end gap-0.5" aria-hidden="true">
          {[1, 2, 3].map((idx) => (
            <span
              key={idx}
              className={`w-1 rounded-sm ${idx === 1 ? 'h-2' : idx === 2 ? 'h-2.5' : 'h-3'} ${
                idx <= bars ? (bars === 1 ? 'bg-[#2EC4B6]' : 'bg-[#6C63FF]') : 'bg-white/20'
              }`}
            />
          ))}
        </span>
        <span>{formatLabel(analysis?.complexity)}</span>
      </Chip>

      <Chip onClick={onInspect}>
        {getPersonaIcon(analysis?.selected_persona)}
        <span>{formatLabel(analysis?.selected_persona)}</span>
      </Chip>

      {analysis?.selected_strategy && (
        <Chip onClick={onInspect}>
          <span>{formatLabel(analysis.selected_strategy)}</span>
        </Chip>
      )}

      <button
        onClick={onInspect}
        className="ml-auto inline-flex items-center gap-1 text-xs text-[#2EC4B6] hover:underline"
      >
        <Info className="h-3.5 w-3.5" /> Inspect Insights
      </button>
    </div>
  );
};
