import { Controller, Get, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { PrismaService } from '../prisma/prisma.service';

@ApiTags('stats')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('stats')
export class StatsController {
  constructor(private prisma: PrismaService) {}

  @Get('strategies')
  async strategies() {
    const outcomes = await this.prisma.signalOutcome.findMany({
      where: { result: { in: ['WIN_TP2', 'WIN_TP1_BE', 'LOSS_SL'] } },
      include: { signal: { include: { symbol: true } } },
    });
    const group = (keyFn: (o: any) => string) => {
      const map: Record<string, any[]> = {};
      for (const o of outcomes as any[]) (map[keyFn(o)] ??= []).push(o);
      const out: Record<string, any> = {};
      for (const [k, rows] of Object.entries(map)) {
        const wins = rows.filter((r) => (r.realizedR ?? 0) > 0);
        const gw = wins.reduce((a, r) => a + (r.realizedR ?? 0), 0);
        const gl = -rows.filter((r) => (r.realizedR ?? 0) < 0).reduce((a, r) => a + (r.realizedR ?? 0), 0);
        const net = rows.reduce((a, r) => a + (r.realizedR ?? 0), 0);
        out[k] = {
          trades: rows.length, win_rate_pct: rows.length ? +(100 * wins.length / rows.length).toFixed(2) : 0,
          profit_factor: gl ? +(gw / gl).toFixed(3) : null,
          net_r: +net.toFixed(3), expectancy_r: rows.length ? +(net / rows.length).toFixed(4) : 0,
          accepted: rows.length >= 100 && gl > 0 && gw / gl >= 1.2 && net > 0,
        };
      }
      return out;
    };
    return {
      by_strategy: group((o) => o.signal?.strategy ?? '?'),
      by_symbol: group((o) => o.signal?.symbol?.symbol ?? '?'),
      by_regime: group((o) => o.signal?.regime ?? 'UNKNOWN'),
      acceptance_rule: '>=100 closed trades, PF>=1.20, positive expectancy & net R, OOS pass',
    };
  }
}
