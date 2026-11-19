import { Body, Controller, Delete, Get, Param, Post, Put, Req, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { PrismaService } from '../prisma/prisma.service';

@ApiTags('users')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('users/me')
export class UsersController {
  constructor(private prisma: PrismaService) {}

  @Get('preferences')
  async getPrefs(@Req() req: any) {
    return this.prisma.userPreference.findUnique({ where: { userId: req.user.id } });
  }

  @Put('preferences')
  async putPrefs(@Req() req: any, @Body() body: any) {
    const data = {
      defaultBalance: body.defaultBalance, riskPerTradePct: body.riskPerTradePct,
      leverage: body.leverage, minScoreAlert: body.minScoreAlert,
      strategies: body.strategies,
    };
    return this.prisma.userPreference.upsert({
      where: { userId: req.user.id }, update: data,
      create: { userId: req.user.id, ...data },
    });
  }

  @Get('watchlist')
  async watchlist(@Req() req: any) {
    return this.prisma.watchlistItem.findMany({ where: { userId: req.user.id } });
  }

  @Post('watchlist')
  async addWatch(@Req() req: any, @Body() body: { symbol: string }) {
    return this.prisma.watchlistItem.upsert({
      where: { userId_symbol: { userId: req.user.id, symbol: body.symbol.toUpperCase() } },
      update: {}, create: { userId: req.user.id, symbol: body.symbol.toUpperCase() },
    });
  }

  @Delete('watchlist/:symbol')
  async removeWatch(@Req() req: any, @Param('symbol') symbol: string) {
    await this.prisma.watchlistItem.deleteMany({
      where: { userId: req.user.id, symbol: symbol.toUpperCase() },
    });
    return { removed: symbol.toUpperCase() };
  }

  @Get('notification-preferences')
  async notifPrefs(@Req() req: any) {
    return this.prisma.notificationPreference.findMany({ where: { userId: req.user.id } });
  }

  @Put('notification-preferences')
  async putNotifPrefs(@Req() req: any, @Body() body: { channel: string; enabled: boolean; telegramChatId?: string }) {
    return this.prisma.notificationPreference.upsert({
      where: { userId_channel: { userId: req.user.id, channel: body.channel } },
      update: { enabled: body.enabled, telegramChatId: body.telegramChatId ?? null },
      create: { userId: req.user.id, channel: body.channel, enabled: body.enabled, telegramChatId: body.telegramChatId ?? null },
    });
  }

  @Get('notifications')
  async notifications(@Req() req: any) {
    return this.prisma.notification.findMany({
      where: { userId: req.user.id }, orderBy: { createdAt: 'desc' }, take: 50,
    });
  }
}
