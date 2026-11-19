import { BadRequestException, Injectable, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Stripe from 'stripe';
import { PrismaService } from '../prisma/prisma.service';

/**
 * Stripe is fully wired but stays dormant until keys are configured
 * ("جهز الكود الآن حتى لو الدفع غير مفعل" — Phase 1 requirement).
 * Without STRIPE_SECRET_KEY, checkout returns 503 with a clear message.
 */
@Injectable()
export class SubscriptionsService {
  private stripe: Stripe | null;

  constructor(private prisma: PrismaService, private config: ConfigService) {
    const key = config.get<string>('STRIPE_SECRET_KEY', '');
    this.stripe = key ? new Stripe(key) : null;
  }

  plans() {
    return {
      plans: [
        { tier: 'FREE', price_usd_month: 0, features: ['إشارات متأخرة 60 دقيقة', '3 إشارات يوميًا', 'تحليل أساسي'] },
        { tier: 'PRO', price_usd_month: 19, features: ['إشارات فورية', 'تحليل كامل + شارت', 'تنبيهات Email', 'Journal'] },
        { tier: 'VIP', price_usd_month: 49, features: ['كل مزايا Pro', 'تنبيهات Telegram', 'إحصاءات متقدمة', 'أولوية'] },
      ],
      payments_enabled: !!this.stripe,
    };
  }

  async me(userId: string) {
    return this.prisma.subscription.findUnique({ where: { userId }, include: { payments: true } });
  }

  async checkout(userId: string, plan: string) {
    if (!this.stripe) {
      throw new ServiceUnavailableException('payments not enabled yet — Stripe keys not configured');
    }
    const priceId = plan === 'VIP'
      ? this.config.get<string>('STRIPE_PRICE_VIP')
      : this.config.get<string>('STRIPE_PRICE_PRO');
    if (!priceId) throw new BadRequestException(`no Stripe price configured for ${plan}`);
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    const frontend = this.config.get<string>('FRONTEND_URL', 'http://localhost:3000');
    const session = await this.stripe.checkout.sessions.create({
      mode: 'subscription',
      customer_email: user?.email,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${frontend}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${frontend}/pricing`,
      metadata: { userId, plan },
    });
    return { checkout_url: session.url };
  }

  async handleWebhook(rawBody: Buffer, signature: string) {
    if (!this.stripe) return { received: true, ignored: 'stripe not configured' };
    const secret = this.config.get<string>('STRIPE_WEBHOOK_SECRET', '');
    let event: Stripe.Event;
    try {
      event = this.stripe.webhooks.constructEvent(rawBody, signature, secret);
    } catch {
      throw new BadRequestException('invalid webhook signature');
    }
    if (event.type === 'checkout.session.completed') {
      const s: any = event.data.object;
      const userId = s.metadata?.userId;
      const plan = s.metadata?.plan ?? 'PRO';
      if (userId) {
        await this.prisma.subscription.upsert({
          where: { userId },
          update: { planTier: plan, status: 'ACTIVE', stripeCustomerId: s.customer, stripeSubscriptionId: s.subscription },
          create: { userId, planTier: plan, status: 'ACTIVE', stripeCustomerId: s.customer, stripeSubscriptionId: s.subscription },
        });
        await this.prisma.user.update({ where: { id: userId }, data: { planTier: plan } });
      }
    }
    if (event.type === 'customer.subscription.deleted') {
      const s: any = event.data.object;
      const sub = await this.prisma.subscription.findFirst({ where: { stripeSubscriptionId: s.id } });
      if (sub) {
        await this.prisma.subscription.update({ where: { id: sub.id }, data: { status: 'CANCELED', planTier: 'FREE' } });
        await this.prisma.user.update({ where: { id: sub.userId }, data: { planTier: 'FREE' } });
      }
    }
    return { received: true };
  }
}
