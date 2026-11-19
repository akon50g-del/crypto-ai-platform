// Pure recipient-selection logic for READY-signal notifications.
// Mirrors the API plan gating: FREE sees signals after 60 minutes.
export const FREE_DELAY_MIN = 60;

export type SignalLike = {
  id: string; symbol: string; strategy: string; score: number;
  status: string; createdAt: Date;
};
export type UserLike = {
  id: string; email: string; planTier: string;
  minScoreAlert: number; strategies: string[];
  watchlist: string[];
  channels: { channel: string; enabled: boolean; telegramChatId?: string | null }[];
};

export type Recipient = { userId: string; channel: string; target: string };

export function selectRecipients(
  signal: SignalLike,
  users: UserLike[],
  alreadySent: Set<string>, // `${userId}:${channel}` with a SENT notification for this signal
  now: Date,
): Recipient[] {
  if (signal.status !== 'READY') return [];
  const ageMin = (now.getTime() - signal.createdAt.getTime()) / 60_000;
  const out: Recipient[] = [];
  for (const u of users) {
    if (u.planTier === 'FREE' && ageMin < FREE_DELAY_MIN) continue;
    if (signal.score < u.minScoreAlert) continue;
    if (u.strategies.length > 0 && !u.strategies.includes(signal.strategy)) continue;
    if (u.watchlist.length > 0 && !u.watchlist.includes(signal.symbol)) continue;
    for (const ch of u.channels) {
      if (!ch.enabled) continue;
      if (alreadySent.has(`${u.id}:${ch.channel}`)) continue;
      if (ch.channel === 'TELEGRAM') {
        if (!ch.telegramChatId) continue;
        out.push({ userId: u.id, channel: 'TELEGRAM', target: ch.telegramChatId });
      } else if (ch.channel === 'EMAIL') {
        out.push({ userId: u.id, channel: 'EMAIL', target: u.email });
      }
    }
  }
  return out;
}
