import { prisma } from '../lib/prisma';

// Public ForexFactory weekly calendar JSON (no API key).
const CALENDAR_URL = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json';

type FFEvent = {
  title: string; country: string; date: string; impact: string;
  forecast?: string; previous?: string;
};

export async function fetchCalendar(): Promise<{ inserted: number; skipped: number }> {
  const res = await fetch(CALENDAR_URL, { headers: { 'User-Agent': 'crypto-ai-signals-worker/0.5' } });
  if (!res.ok) throw new Error(`calendar fetch failed: HTTP ${res.status}`);
  const events = (await res.json()) as FFEvent[];
  let inserted = 0, skipped = 0;
  for (const e of events) {
    if (e.country !== 'USD') { skipped++; continue; }
    const impact = e.impact === 'High' ? 'HIGH' : e.impact === 'Medium' ? 'MEDIUM' : 'LOW';
    if (impact === 'LOW') { skipped++; continue; }
    const scheduledAt = new Date(e.date);
    const exists = await prisma.economicEvent.findFirst({ where: { title: e.title, scheduledAt } });
    if (exists) { skipped++; continue; }
    await prisma.economicEvent.create({
      data: {
        title: e.title, currency: 'USD', impact, scheduledAt,
        forecast: e.forecast || null, previous: e.previous || null,
      },
    });
    inserted++;
  }
  return { inserted, skipped };
}
