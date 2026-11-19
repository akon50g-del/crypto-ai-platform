// Deterministic news classification (no LLM in daily operation).
// Impact keywords reflect the macro events the strategy blackout cares about.
const HIGH_KEYWORDS = [
  'cpi', 'inflation', 'fomc', 'fed ', 'federal reserve', 'rate cut', 'rate hike',
  'interest rate', 'nonfarm', 'payroll', 'jobs report', 'gdp', 'pce', 'ppi',
  'sec ', 'etf approval', 'etf rejected', 'lawsuit', 'bankruptcy', 'hack', 'exploit',
  'halving', 'powell', 'treasury', 'default', 'recession',
];
const LOW_KEYWORDS = ['price prediction', 'opinion', 'explained', 'how to', 'guide', 'weekly'];

const SYMBOL_KEYWORDS: Record<string, string[]> = {
  BTCUSDT: ['bitcoin', 'btc'],
  ETHUSDT: ['ethereum', 'eth'],
  SOLUSDT: ['solana', 'sol'],
  XRPUSDT: ['xrp', 'ripple'],
  BNBUSDT: ['bnb', 'binance coin'],
  DOGEUSDT: ['dogecoin', 'doge'],
  LINKUSDT: ['chainlink', 'link'],
  AVAXUSDT: ['avalanche', 'avax'],
};

const POSITIVE = ['surge', 'rally', 'approval', 'approved', 'bullish', 'record high', 'inflow', 'partnership', 'upgrade'];
const NEGATIVE = ['crash', 'plunge', 'bearish', 'outflow', 'ban', 'hack', 'exploit', 'lawsuit', 'rejected', 'selloff', 'liquidation'];

export function classifyImpact(title: string): 'HIGH' | 'MEDIUM' | 'LOW' {
  const t = ` ${title.toLowerCase()} `;
  if (HIGH_KEYWORDS.some((k) => t.includes(k))) return 'HIGH';
  if (LOW_KEYWORDS.some((k) => t.includes(k))) return 'LOW';
  return 'MEDIUM';
}

export function extractSymbols(title: string): string[] {
  const t = ` ${title.toLowerCase()} `;
  return Object.entries(SYMBOL_KEYWORDS)
    .filter(([, kws]) => kws.some((k) => t.includes(` ${k}`) || t.includes(`${k} `) || t.includes(` ${k} `)))
    .map(([s]) => s);
}

export function sentimentScore(title: string): number {
  const t = title.toLowerCase();
  const pos = POSITIVE.filter((k) => t.includes(k)).length;
  const neg = NEGATIVE.filter((k) => t.includes(k)).length;
  if (pos === neg) return 0;
  return Math.max(-1, Math.min(1, (pos - neg) / Math.max(pos + neg, 1)));
}

/** News blackout: ±30 minutes around HIGH-impact scheduled events (strategy filter). */
export function isBlackout(events: { scheduledAt: Date; impact: string }[], now: Date, minutes = 30): boolean {
  return events.some(
    (e) => e.impact === 'HIGH' && Math.abs(e.scheduledAt.getTime() - now.getTime()) <= minutes * 60_000,
  );
}
