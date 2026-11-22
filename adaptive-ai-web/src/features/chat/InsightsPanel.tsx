import React from 'react';
import type { MessageItem } from '../../api/types';
import { GlassPanel } from '../../components/glass/GlassPanel';
import { computeAScore, formatLabel, formatScorePct } from '../../lib/formatters';

interface Props {
  message: MessageItem | null;
  onClose: () => void;
}

export const InsightsPanel: React.FC<Props> = ({ message, onClose }) => {
  if (!message) return null;
  const analysis = message.analysis;
  const aScore = message.a_score || computeAScore(analysis, true);

  return (
    <GlassPanel title="Adaptive Insights" subtitle="v3 Orchestration & Adaptation" onClose={onClose}>
      <div className="space-y-4 text-xs">
        <div className="grid grid-cols-2 gap-2">
          <div className="glass rounded-xl p-3">
            <div className="opacity-65">Task / Intent</div>
            <div className="mt-0.5 font-semibold">{formatLabel(analysis?.task_type)}</div>
          </div>
          <div className="glass rounded-xl p-3">
            <div className="opacity-65">Complexity</div>
            <div className="mt-0.5 font-semibold">{formatLabel(analysis?.complexity)}</div>
          </div>
          <div className="glass rounded-xl p-3">
            <div className="opacity-65">Persona</div>
            <div className="mt-0.5 font-semibold">{formatLabel(analysis?.selected_persona)}</div>
          </div>
          <div className="glass rounded-xl p-3">
            <div className="opacity-65">Strategy</div>
            <div className="mt-0.5 font-semibold">{formatLabel(analysis?.selected_strategy)}</div>
          </div>
        </div>

        <div className="glass rounded-xl p-3.5">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-semibold">A-Score Heuristic</span>
            <span className="font-mono text-sm font-bold text-[#2EC4B6]">{aScore.total.toFixed(2)}</span>
          </div>
          <div className="mb-2 font-mono text-[10px] opacity-65">A = 0.30I + 0.25C + 0.25P + 0.20H</div>
          <div className="my-2 flex justify-center">
            <svg width="132" height="74" viewBox="0 0 132 74" aria-label="A-Score Gauge">
              <defs>
                <linearGradient id="reactGaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#6C63FF" />
                  <stop offset="100%" stopColor="#2EC4B6" />
                </linearGradient>
              </defs>
              <path d="M 16 64 A 50 50 0 0 1 116 64" fill="none" stroke="rgba(248,250,252,0.14)" strokeWidth="9" strokeLinecap="round" />
              <path
                d="M 16 64 A 50 50 0 0 1 116 64"
                fill="none"
                stroke="url(#reactGaugeGrad)"
                strokeWidth="9"
                strokeLinecap="round"
                strokeDasharray="126"
                strokeDashoffset={126 * (1 - Math.max(0, Math.min(1, aScore.total)))}
              />
              <g transform={`translate(66,64) rotate(${-90 + Math.max(0, Math.min(1, aScore.total)) * 180})`}>
                <line x1="0" y1="0" x2="0" y2="-36" stroke="#F8FAFC" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="0" cy="0" r="4.5" fill="#2EC4B6" stroke="#121826" strokeWidth="1.5" />
              </g>
            </svg>
          </div>
          {(['I', 'C', 'P', 'H'] as const).map((key) => (
            <div key={key} className="mb-1.5">
              <div className="flex justify-between text-[11px]">
                <span>{key} Component</span>
                <span className="font-mono">{aScore[key].toFixed(2)}</span>
              </div>
              <div className="mt-0.5 h-1.5 rounded-full bg-white/10">
                <div className="h-1.5 rounded-full bg-[#6C63FF]" style={{ width: `${Math.round(aScore[key] * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>

        {message.evaluation && (
          <div className="glass rounded-xl p-3.5 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold">Structural Evaluation</span>
              <span className="font-mono text-[#2EC4B6]">{formatScorePct(message.evaluation.quality_score)}</span>
            </div>
            <div className="text-[11px] opacity-75">Status: {formatLabel(message.evaluation.evaluation_status)}</div>
            {message.evaluation.warnings && message.evaluation.warnings.length > 0 && (
              <ul className="list-disc pl-4 text-[11px] text-amber-300">
                {message.evaluation.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="glass rounded-xl p-3.5 space-y-1.5">
          <div className="font-semibold">Runtime & Adaptation</div>
          <div className="flex justify-between gap-2">
            <span className="opacity-70">Model</span>
            <span className="font-mono text-right">{message.meta?.model || 'mock'}</span>
          </div>
          <div className="flex justify-between">
            <span className="opacity-70">Latency</span>
            <span className="font-mono">{message.meta?.latency_ms ?? 0} ms</span>
          </div>
          <div className="flex justify-between">
            <span className="opacity-70">Adaptation</span>
            <span>{formatLabel(analysis?.adaptation?.method || 'default')}</span>
          </div>
        </div>
      </div>
    </GlassPanel>
  );
};
