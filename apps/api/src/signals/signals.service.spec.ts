import { applyPlanLimits } from './signals.service';

describe('applyPlanLimits', () => {
  const now = new Date('2026-11-19T12:00:00Z');
  const mk = (minutesAgo: number) => ({ createdAt: new Date(now.getTime() - minutesAgo * 60_000) });

  it('FREE hides signals newer than 60 minutes and caps at 3', () => {
    const rows = [mk(5), mk(30), mk(61), mk(90), mk(120), mk(180)];
    const out = applyPlanLimits(rows, 'FREE', now);
    expect(out).toHaveLength(3);
    expect(out[0].createdAt).toEqual(mk(61).createdAt);
  });

  it('PRO sees everything immediately', () => {
    const rows = [mk(1), mk(2), mk(3), mk(4)];
    expect(applyPlanLimits(rows, 'PRO', now)).toHaveLength(4);
  });

  it('unknown plan falls back to FREE limits', () => {
    expect(applyPlanLimits([mk(1)], 'UNKNOWN', now)).toHaveLength(0);
  });
});
