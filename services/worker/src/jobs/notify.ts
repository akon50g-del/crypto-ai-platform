import { formatSignalAlert } from '../lib/format';
import { prisma } from '../lib/prisma';
import { selectRecipients, type UserLike } from '../lib/recipients';
import { sendEmail } from '../senders/email';
import { sendTelegram } from '../senders/telegram';

const LOOKBACK_HOURS = 24;

/** Find READY signals from the last 24h and notify eligible users.
 *  Dedupe is by SENT notifications only, so dry-run/failed rows retry
 *  once real credentials exist. */
export async function notifyReadySignals(now = new Date()): Promise<{
  signals: number; sent: number; dryRun: number; failed: number;
}> {
  const since = new Date(now.getTime() - LOOKBACK_HOURS * 3600_000);
  const signals = await prisma.signal.findMany({
    where: { status: 'READY', createdAt: { gte: since } },
    include: { symbol: true },
    orderBy: { createdAt: 'asc' },
  });
  const users = await prisma.user.findMany({
    include: { preferences: true, watchlist: true, notificationPrefs: true },
  });
  const userLikes: UserLike[] = users.map((u) => ({
    id: u.id, email: u.email, planTier: u.planTier,
    minScoreAlert: u.preferences?.minScoreAlert ?? 7,
    strategies: Array.isArray(u.preferences?.strategies) ? (u.preferences!.strategies as string[]) : [],
    watchlist: u.watchlist.map((w) => w.symbol),
    channels: u.notificationPrefs.map((p) => ({
      channel: p.channel, enabled: p.enabled, telegramChatId: p.telegramChatId,
    })),
  }));

  let sent = 0, dryRun = 0, failed = 0;
  for (const signal of signals) {
    const sentRows = await prisma.notification.findMany({
      where: { signalId: signal.id, status: 'SENT' },
      select: { userId: true, channel: true },
    });
    // Dry-run rows (no credentials configured) also dedupe, so the 1-minute
    // job does not spam rows; real send failures still retry.
    const dryRows = await prisma.notification.findMany({
      where: { signalId: signal.id, status: 'FAILED', error: { startsWith: 'dry-run' } },
      select: { userId: true, channel: true },
    });
    const alreadySent = new Set([
      ...sentRows.map((r) => `${r.userId}:${r.channel}`),
      ...dryRows.map((r) => `${r.userId}:${r.channel}`),
    ]);
    const symbolName = signal.symbol.symbol;
    const recipients = selectRecipients(
      { id: signal.id, symbol: symbolName, strategy: signal.strategy, score: signal.score, status: signal.status, createdAt: signal.createdAt },
      userLikes, alreadySent, now,
    );
    const { title, body } = formatSignalAlert({ ...signal, symbol: symbolName });
    for (const r of recipients) {
      const result = r.channel === 'TELEGRAM'
        ? await sendTelegram(r.target, body)
        : await sendEmail(r.target, title, body);
      await prisma.notification.create({
        data: {
          userId: r.userId, signalId: signal.id, channel: r.channel,
          status: result.ok ? 'SENT' : 'FAILED',
          title, body,
          sentAt: result.ok ? new Date() : null,
          error: result.ok ? null : result.error ?? 'send failed',
        },
      });
      if (result.ok) sent++; else if (result.dryRun) dryRun++; else failed++;
    }
  }
  return { signals: signals.length, sent, dryRun, failed };
}
