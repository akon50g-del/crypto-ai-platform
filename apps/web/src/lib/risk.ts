// Client-side mirror of the engine's position_size.py (Phase 2 risk.py).
export function positionSize(balance: number, riskPct: number, entry: number, sl: number,
                             targets: number[] = [], leverage = 3) {
  const dist = Math.abs(entry - sl);
  if (!dist || !balance) return null;
  const side = sl > entry ? 'SHORT' : 'LONG';
  const riskAmount = (balance * riskPct) / 100;
  const qty = riskAmount / dist;
  const notional = qty * entry;
  return {
    side, riskAmount, qty, notional,
    margin: notional / leverage,
    slDistancePct: (dist / entry) * 100,
    targets: targets.map((t) => ({
      price: t,
      pnl: (side === 'SHORT' ? entry - t : t - entry) * qty,
      rr: Math.abs(t - entry) / dist,
    })),
  };
}
