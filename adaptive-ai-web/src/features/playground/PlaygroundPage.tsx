import React, { useState } from 'react';
import { FlaskConical } from 'lucide-react';
import { useAnalyze } from '../../hooks/useAdaptiveApi';
import { useAppStore } from '../../store/useAppStore';
import { GlassCard } from '../../components/glass/GlassCard';
import { GlassButton } from '../../components/glass/GlassButton';
import { computeAScore, formatLabel } from '../../lib/formatters';

export const PlaygroundPage: React.FC = () => {
  const [prompt, setPrompt] = useState('Design a scalable FastAPI backend with caching and explain trade-offs');
  const { sessionId, userId } = useAppStore();
  const analyzeMut = useAnalyze();
  const aScore = analyzeMut.data ? computeAScore(analyzeMut.data, false) : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6 md:p-8">
      <div>
        <h1 className="text-2xl font-bold">Analyze Playground</h1>
        <p className="text-sm opacity-75">
          Test <code>POST /api/v1/assistant/analyze</code> on the v3 backend without triggering a model call.
        </p>
      </div>

      <GlassCard level="elevated" className="space-y-4 p-5">
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="glass w-full rounded-xl p-3 text-sm outline-none focus:border-[#6C63FF]"
        />
        <GlassButton
          onClick={() => analyzeMut.mutate({ message: prompt, session_id: sessionId, user_id: userId })}
          disabled={analyzeMut.isPending}
        >
          <FlaskConical className="h-4 w-4" />
          {analyzeMut.isPending ? 'Analyzing...' : 'Run Analysis'}
        </GlassButton>
      </GlassCard>

      {analyzeMut.data && aScore && (
        <GlassCard className="grid gap-4 p-5 sm:grid-cols-2">
          <div>
            <div className="text-xs opacity-65">Task Type</div>
            <div className="text-lg font-semibold">{formatLabel(analyzeMut.data.task_type)}</div>
          </div>
          <div>
            <div className="text-xs opacity-65">Complexity</div>
            <div className="text-lg font-semibold">{formatLabel(analyzeMut.data.complexity)}</div>
          </div>
          <div>
            <div className="text-xs opacity-65">Selected Persona</div>
            <div className="text-lg font-semibold">{formatLabel(analyzeMut.data.selected_persona)}</div>
          </div>
          <div>
            <div className="text-xs opacity-65">Selected Strategy</div>
            <div className="text-lg font-semibold">{formatLabel(analyzeMut.data.selected_strategy)}</div>
          </div>
          <div className="sm:col-span-2 border-t border-white/10 pt-3 flex items-center justify-between text-sm">
            <span>A-Score (0.30I + 0.25C + 0.25P + 0.20H)</span>
            <span className="font-mono font-bold text-[#2EC4B6]">{aScore.total.toFixed(2)}</span>
          </div>
        </GlassCard>
      )}
    </div>
  );
};
