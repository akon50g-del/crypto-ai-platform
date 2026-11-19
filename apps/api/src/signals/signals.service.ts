import { Injectable, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { DISCLAIMER_AR, PLAN_LIMITS } from '../common/constants';
import { PrismaService } from '../prisma/prisma.service';

/** Pure plan-gating logic (unit-tested): Free = delayed + daily-capped. */
export function applyPlanLimits<T extends { createdAt: Date | string }>(
  signals: T[], plan: string, now: Date = new Date(),
): T[] {
  const limits = PLAN_LIMITS[plan] ?? PLAN_LIMITS.FREE;
  const cutoff = new Date(now.getTime() - limits.delayMinutes * 60_000);
  return signals
    .filter((s) => new Date(s.createdAt) <= cutoff)
    .slice(0, limits.dailySignals);
}

@Injectable()
export class SignalsService {
  constructor(private prisma: PrismaService, private config: ConfigService) {}

  async list(plan: string, filters: { status?: string; strategy?: string; symbol?: string }) {
    const where: any = {};
    if (filters.status) where.status = filters.status;
    if (filters.strategy) where.strategy = filters.strategy;
    if (filters.symbol) {
      const sym = await this.prisma.symbol.findUnique({ where: { symbol: filters.symbol } });
      if (!sym) return { signals: [], disclaimer: DISCLAIMER_AR };
      where.symbolId = sym.id;
    }
    const rows = await this.prisma.signal.findMany({
      where, orderBy: { createdAt: 'desc' }, take: 200,
      include: { symbol: true, outcome: true },
    });
    const visible = applyPlanLimits(rows, plan);
    return {
      signals: visible.map((s: any) => this.serialize(s, plan)),
      plan, delayed_minutes: (PLAN_LIMITS[plan] ?? PLAN_LIMITS.FREE).delayMinutes,
      disclaimer: DISCLAIMER_AR,
    };
  }

  async detail(id: string, plan: string) {
    const s = await this.prisma.signal.findUnique({
      where: { id }, include: { symbol: true, outcome: true, analysis: true },
    });
    if (!s) throw new NotFoundException('signal not found');
    const full = (PLAN_LIMITS[plan] ?? PLAN_LIMITS.FREE).fullAnalysis;
    const base = this.serialize(s, plan);
    return {
      ...base,
      analysis: full ? (s as any).analysis : null,
      analysis_locked: !full,
      disclaimer: DISCLAIMER_AR,
    };
  }

  async latestAnalysis(symbol: string, plan: string) {
    const sym = await this.prisma.symbol.findUnique({ where: { symbol } });
    if (!sym) throw new NotFoundException('symbol not found');
    const analysis = await this.prisma.analysis.findFirst({
      where: { symbolId: sym.id }, orderBy: { createdAt: 'desc' },
    });
    const full = (PLAN_LIMITS[plan] ?? PLAN_LIMITS.FREE).fullAnalysis;
    return {
      symbol, analysis: full ? analysis : (analysis ? {
        id: analysis.id, bias: analysis.bias, regime: analysis.regime,
        priceAtAnalysis: analysis.priceAtAnalysis, createdAt: analysis.createdAt,
      } : null),
      analysis_locked: !full, disclaimer: DISCLAIMER_AR,
    };
  }

  async candles(symbol: string, tf: string, limit: number) {
    const base = this.config.get<string>('BINANCE_BASE_URL', 'https://data-api.binance.vision');
    const res = await fetch(`${base}/api/v3/klines?symbol=${symbol}&interval=${tf}&limit=${limit}`);
    if (!res.ok) throw new NotFoundException('candles unavailable');
    const rows: any[] = await res.json();
    // Drop the still-forming candle (Skills rule: closed candles only)
    const closed = rows.slice(0, -1);
    return {
      symbol, timeframe: tf, source: 'binance',
      candles: closed.map((r) => ({
        t: r[0], o: +r[1], h: +r[2], l: +r[3], c: +r[4], v: +r[5],
      })),
    };
  }

  private serialize(s: any, plan: string) {
    return {
      id: s.id, symbol: s.symbol?.symbol, strategy: s.strategy, side: s.side,
      status: s.status, score: s.score, grade: s.grade, regime: s.regime,
      score_breakdown: s.scoreBreakdown,
      entry_zone: [s.entryZoneLow, s.entryZoneHigh], entry_price: s.entryPrice,
      stop_loss: s.stopLoss, tp1: s.tp1, tp2: s.tp2,
      rr_tp1: s.rrTp1, rr_tp2: s.rrTp2, invalidation: s.invalidationPrice,
      reason_ar: s.reasonAr, reason_en: s.reasonEn,
      outcome: s.outcome ? { result: s.outcome.result, realized_r: s.outcome.realizedR } : null,
      created_at: s.createdAt, ready_at: s.readyAt, expires_at: s.expiresAt,
      plan,
    };
  }
}
