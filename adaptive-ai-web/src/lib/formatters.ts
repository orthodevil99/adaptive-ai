import type { AScoreBreakdown, BackendAnalysis } from '../api/types';

export function formatLabel(raw?: string | null): string {
  if (!raw) return 'General';
  return raw
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ');
}

export function formatScorePct(val: number): string {
  return `${Math.round(val * 100)}%`;
}

export function computeAScore(analysis?: BackendAnalysis, hasHistory = false): AScoreBreakdown {
  if (!analysis) {
    return { I: 0.75, C: 0.75, P: 0.80, H: 0.65, total: 0.75 };
  }
  const I = Number(Math.min(0.99, Math.max(0.5, analysis.confidence ?? 0.85)).toFixed(2));
  const C = Number(
    (analysis.complexity === 'high' ? 0.92 : analysis.complexity === 'medium' ? 0.78 : 0.65).toFixed(2)
  );
  const P = Number((analysis.adaptation?.method === 'thompson' ? 0.92 : 0.86).toFixed(2));
  const H = hasHistory ? 0.82 : 0.64;
  const total = Number((0.30 * I + 0.25 * C + 0.25 * P + 0.20 * H).toFixed(2));
  return { I, C, P, H, total };
}
