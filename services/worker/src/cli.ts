// Run one job immediately (no Redis needed): npm run job:news | job:calendar | job:notify
import { fetchCalendar } from './jobs/calendar';
import { fetchNews } from './jobs/news';
import { notifyReadySignals } from './jobs/notify';
import { prisma } from './lib/prisma';

async function main() {
  const job = process.argv[2];
  const runners: Record<string, () => Promise<any>> = {
    news: fetchNews, calendar: fetchCalendar, notify: () => notifyReadySignals(),
  };
  if (!runners[job]) {
    console.error('usage: cli.ts <news|calendar|notify>');
    process.exit(1);
  }
  console.log(await runners[job]());
  await prisma.$disconnect();
}
main();
