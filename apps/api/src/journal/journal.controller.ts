import { Body, Controller, Delete, Get, Param, Patch, Post, Req, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { PrismaService } from '../prisma/prisma.service';

/** Trade journal — actual exit price/quantity/fees only, never assumed
 *  (journal.md rule from the Skills). */
@ApiTags('journal')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('journal')
export class JournalController {
  constructor(private prisma: PrismaService) {}

  @Get()
  list(@Req() req: any) {
    return this.prisma.tradeJournalEntry.findMany({
      where: { userId: req.user.id }, orderBy: { openedAt: 'desc' },
    });
  }

  @Post()
  create(@Req() req: any, @Body() body: any) {
    return this.prisma.tradeJournalEntry.create({
      data: {
        userId: req.user.id, symbol: body.symbol, side: body.side,
        strategy: body.strategy ?? null, entryPrice: body.entryPrice,
        stopLoss: body.stopLoss ?? null, tp1: body.tp1 ?? null, tp2: body.tp2 ?? null,
        exitPrice: body.exitPrice ?? null, quantity: body.quantity ?? null,
        fees: body.fees ?? null, pnlUsd: body.pnlUsd ?? null,
        realizedR: body.realizedR ?? null, reason: body.reason ?? null,
        screenshotUrl: body.screenshotUrl ?? null,
        openedAt: body.openedAt ? new Date(body.openedAt) : new Date(),
        closedAt: body.closedAt ? new Date(body.closedAt) : null,
      },
    });
  }

  @Patch(':id')
  async update(@Req() req: any, @Param('id') id: string, @Body() body: any) {
    const { id: _x, userId: _u, ...data } = body;
    if (data.closedAt) data.closedAt = new Date(data.closedAt);
    return this.prisma.tradeJournalEntry.updateMany({
      where: { id, userId: req.user.id }, data,
    });
  }

  @Delete(':id')
  async remove(@Req() req: any, @Param('id') id: string) {
    await this.prisma.tradeJournalEntry.deleteMany({ where: { id, userId: req.user.id } });
    return { removed: id };
  }
}
