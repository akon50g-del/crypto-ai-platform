// String constants mirroring the PostgreSQL enums in the canonical schema.
// (SQLite dev schema stores these as String; Postgres schema uses real enums.)
export const PlanTier = { FREE: 'FREE', PRO: 'PRO', VIP: 'VIP' } as const;
export type PlanTierValue = (typeof PlanTier)[keyof typeof PlanTier];

export const APPROVED_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT',
  'BNBUSDT', 'DOGEUSDT', 'LINKUSDT', 'AVAXUSDT',
];

// Plan gating (ARCHITECTURE.md §5): Free sees delayed + capped signals.
export const PLAN_LIMITS: Record<string, { delayMinutes: number; dailySignals: number; fullAnalysis: boolean }> = {
  FREE: { delayMinutes: 60, dailySignals: 3, fullAnalysis: false },
  PRO: { delayMinutes: 0, dailySignals: 1000, fullAnalysis: true },
  VIP: { delayMinutes: 0, dailySignals: 1000, fullAnalysis: true },
};

export const DISCLAIMER_AR = 'التحليل تعليمي وليس نصيحة مالية، والتداول عالي المخاطر.';
