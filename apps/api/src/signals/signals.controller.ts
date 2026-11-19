import { Controller, Get, Param, Query, Req, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiQuery, ApiTags } from '@nestjs/swagger';
import { SignalsService } from './signals.service';

@ApiTags('signals')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller()
export class SignalsController {
  constructor(private signals: SignalsService) {}

  @Get('signals')
  @ApiQuery({ name: 'status', required: false })
  @ApiQuery({ name: 'strategy', required: false })
  @ApiQuery({ name: 'symbol', required: false })
  list(@Req() req: any, @Query('status') status?: string,
       @Query('strategy') strategy?: string, @Query('symbol') symbol?: string) {
    return this.signals.list(req.user.plan ?? 'FREE', { status, strategy, symbol });
  }

  @Get('signals/:id')
  detail(@Req() req: any, @Param('id') id: string) {
    return this.signals.detail(id, req.user.plan ?? 'FREE');
  }

  @Get('coins/:symbol/analysis')
  analysis(@Req() req: any, @Param('symbol') symbol: string) {
    return this.signals.latestAnalysis(symbol.toUpperCase(), req.user.plan ?? 'FREE');
  }

  @Get('coins/:symbol/candles')
  @ApiQuery({ name: 'tf', required: false, example: '1h' })
  @ApiQuery({ name: 'limit', required: false, example: 200 })
  candles(@Param('symbol') symbol: string, @Query('tf') tf = '1h',
          @Query('limit') limit = '200') {
    return this.signals.candles(symbol.toUpperCase(), tf, Math.min(+limit || 200, 1000));
  }
}
