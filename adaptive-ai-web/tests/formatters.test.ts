import { describe, expect, it } from 'vitest';
import { formatLabel, formatScorePct } from '../src/lib/formatters';

describe('formatters', () => {
  it('formats snake_case labels cleanly', () => {
    expect(formatLabel('step_by_step_explanation')).toBe('Step By Step Explanation');
    expect(formatLabel('creative_writing')).toBe('Creative Writing');
  });

  it('formats normalized scores as percentages', () => {
    expect(formatScorePct(0.924)).toBe('92%');
  });
});
