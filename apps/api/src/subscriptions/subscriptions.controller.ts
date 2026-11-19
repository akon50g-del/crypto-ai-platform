import { Body, Controller, Get, Headers, HttpCode, Post, Req, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { SubscriptionsService } from './subscriptions.service';

@ApiTags('subscriptions')
@Controller('subscriptions')
export class SubscriptionsController {
  constructor(private subs: SubscriptionsService) {}

  @Get('plans')
  plans() {
    return this.subs.plans();
  }

  @ApiBearerAuth()
  @UseGuards(AuthGuard('jwt'))
  @Get('me')
  me(@Req() req: any) {
    return this.subs.me(req.user.id);
  }

  @ApiBearerAuth()
  @UseGuards(AuthGuard('jwt'))
  @Post('checkout')
  checkout(@Req() req: any, @Body() body: { plan: string }) {
    return this.subs.checkout(req.user.id, body.plan);
  }

  // Stripe webhook: raw body is preserved in main.ts for signature checks.
  @Post('webhook')
  @HttpCode(200)
  webhook(@Req() req: any, @Headers('stripe-signature') signature: string) {
    return this.subs.handleWebhook(req.rawBody ?? Buffer.from(JSON.stringify(req.body)), signature);
  }
}
