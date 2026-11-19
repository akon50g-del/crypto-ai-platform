export type SendResult = { ok: boolean; dryRun?: boolean; error?: string };

/** Telegram Bot API sender. Without TELEGRAM_BOT_TOKEN it is a dry-run:
 *  the notification is recorded but nothing is sent (never fakes success). */
export async function sendTelegram(chatId: string, text: string): Promise<SendResult> {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) return { ok: false, dryRun: true, error: 'dry-run: TELEGRAM_BOT_TOKEN not set' };
  try {
    const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text }),
    });
    const data: any = await res.json().catch(() => ({}));
    return res.ok && data.ok ? { ok: true } : { ok: false, error: data.description ?? `HTTP ${res.status}` };
  } catch (e: any) {
    return { ok: false, error: e.message };
  }
}
