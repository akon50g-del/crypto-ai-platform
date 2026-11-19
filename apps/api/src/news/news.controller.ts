import { Controller, Get, Query, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { PrismaService } from '../prisma/prisma.service';

@ApiTags('news')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller()
export class NewsController {
  constructor(private prisma: PrismaService) {}

  @Get('news')
  async news(@Query('symbol') symbol?: string) {
    const rows = await this.prisma.newsItem.findMany({
      orderBy: { publishedAt: 'desc' }, take: 50,
    });
    const filtered = symbol
      ? rows.filter((r: any) => JSON.stringify(r.symbols ?? []).includes(symbol.replace('USDT', '')))
      : rows;
    return { news: filtered };
  }

  @Get('calendar')
  async calendar() {
    const rows = await this.prisma.economicEvent.findMany({
      where: { scheduledAt: { gte: new Date() } },
      orderBy: { scheduledAt: 'asc' }, take: 50,
    });
    return { events: rows };
  }
}
