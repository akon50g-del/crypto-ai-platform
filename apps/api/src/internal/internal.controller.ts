import { Body, Controller, Headers, Post, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ApiExcludeController } from '@nestjs/swagger';
import { PrismaService } from '../prisma/prisma.service';
import { SignalsGateway } from './signals.gateway';

/** Internal write path for the AI Engine (alternative to direct DB writes).
 *  Protected by X-Internal-Token when AI_ENGINE_INTERNAL_TOKEN is set. */
@ApiExcludeController()
@Controller('internal')
export class InternalController {
  constructor(private prisma: PrismaService, private config: ConfigService,
              private gateway: SignalsGateway) {}

  private check(token?: string) {
    const expected = this.config.get<string>('AI_ENGINE_INTERNAL_TOKEN', '');
    if (expected && token !== expected) throw new UnauthorizedException('invalid internal token');
  }

  @Post('signals')
  async createSignal(@Headers('x-internal-token') token: string, @Body() body: any) {
    this.check(token);
    const sym = await this.prisma.symbol.upsert({
      where: { symbol: body.symbol },
      update: {}, create: { symbol: body.symbol, baseAsset: body.symbol.replace('USDT', '') },
    });
    const signal = await this.prisma.signal.create({
      data: {
        symbolId: sym.id, strategy: body.strategy, side: body.side,
        status: body.status ?? 'WATCH', score: body.score,
        scoreBreakdown: body.scoreBreakdown ?? {}, grade: body.grade ?? null,
        regime: body.regime ?? 'UNKNOWN',
        entryZoneLow: body.entryZoneLow, entryZoneHigh: body.entryZoneHigh,
        stopLoss: body.stopLoss, tp1: body.tp1, tp2: body.tp2,
        rrTp1: body.rrTp1 ?? null, rrTp2: body.rrTp2 ?? null,
        invalidationPrice: body.invalidation ?? null,
        reasonAr: body.reasonAr, reasonEn: body.reasonEn ?? null,
        readyAt: body.status === 'READY' ? new Date() : null,
        outcome: { create: { result: 'OPEN' } },
      },
      include: { symbol: true },
    });
    if (signal.status === 'READY') this.gateway.broadcastSignal(signal);
    return signal;
  }

  @Post('outcomes')
  async updateOutcome(@Headers('x-internal-token') token: string, @Body() body: any) {
    this.check(token);
    const outcome = await this.prisma.signalOutcome.update({
      where: { signalId: body.signalId },
      data: {
        result: body.result, exitPrice: body.exitPrice ?? null,
        realizedR: body.realizedR ?? null, closedAt: new Date(),
      },
    });
    await this.prisma.signal.update({
      where: { id: body.signalId }, data: { status: 'CLOSED', closedAt: new Date() },
    });
    return outcome;
  }
}
