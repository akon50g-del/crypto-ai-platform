import { Controller, Get, Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AuthModule } from './auth/auth.module';
import { InternalController } from './internal/internal.controller';
import { SignalsGateway } from './internal/signals.gateway';
import { JournalController } from './journal/journal.controller';
import { NewsController } from './news/news.controller';
import { PrismaModule } from './prisma/prisma.module';
import { SignalsModule } from './signals/signals.module';
import { StatsController } from './stats/stats.controller';
import { SubscriptionsController } from './subscriptions/subscriptions.controller';
import { SubscriptionsService } from './subscriptions/subscriptions.service';
import { UsersController } from './users/users.controller';

@Controller()
class HealthController {
  @Get('health')
  health() {
    return { status: 'ok', service: 'api', time_utc: new Date().toISOString() };
  }
}

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    AuthModule,
    SignalsModule,
  ],
  controllers: [
    HealthController, UsersController, SubscriptionsController,
    NewsController, JournalController, StatsController, InternalController,
  ],
  providers: [SubscriptionsService, SignalsGateway],
})
export class AppModule {}
