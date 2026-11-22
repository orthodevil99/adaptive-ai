import React from 'react';
import { useAnalyticsSummary, useHealth, useModelHealth, useProjectInfo } from '../../hooks/useAdaptiveApi';
import { GlassCard } from '../../components/glass/GlassCard';

export const StatusPage: React.FC = () => {
  const { data: info } = useProjectInfo();
  const { data: health } = useHealth();
  const { data: model } = useModelHealth();
  const { data: analytics } = useAnalyticsSummary();

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6 md:p-8">
      <div>
        <h1 className="text-2xl font-bold">System & Model Status</h1>
        <p className="text-sm opacity-75">Live connectivity to <code>adaptive_ai_v3</code> and Thompson-sampling analytics.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <GlassCard className="p-5">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs uppercase opacity-65">Backend API</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2EC4B6]">
              <span className="h-2 w-2 rounded-full bg-[#2EC4B6]" />
              {String(health?.status || 'checking')}
            </span>
          </div>
          <pre className="mt-2 overflow-x-auto text-[11px] opacity-80">{JSON.stringify(health || {}, null, 2)}</pre>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs uppercase opacity-65">LLM Provider</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2EC4B6]">
              <span className="h-2 w-2 rounded-full bg-[#2EC4B6]" />
              {String(model?.provider || 'checking')}
            </span>
          </div>
          <pre className="mt-2 overflow-x-auto text-[11px] opacity-80">{JSON.stringify(model || {}, null, 2)}</pre>
        </GlassCard>
      </div>

      {info && (
        <GlassCard className="p-5 text-xs">
          <h2 className="mb-2 text-sm font-semibold">Service Info</h2>
          <pre className="overflow-x-auto opacity-80">{JSON.stringify(info, null, 2)}</pre>
        </GlassCard>
      )}

      {analytics && (
        <GlassCard className="p-5 text-xs">
          <h2 className="mb-2 text-sm font-semibold">Adaptation & Usage Analytics</h2>
          <pre className="overflow-x-auto opacity-80">{JSON.stringify(analytics, null, 2)}</pre>
        </GlassCard>
      )}
    </div>
  );
};
