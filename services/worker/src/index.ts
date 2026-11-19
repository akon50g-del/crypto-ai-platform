import { Queue, Worker } from 'bullmq';
import IORedis from 'ioredis';
import { fetchCalendar } from './jobs/calendar';
import { fetchNews } from './jobs/news';
import { notifyReadySignals } from './jobs/notify';

const JOBS = {
  news: { run: fetchNews, everyMs: Number(process.env.NEWS_EVERY_MIN ?? 15) * 60_000 },
  calendar: { run: fetchCalendar, everyMs: Number(process.env.CALENDAR_EVERY_HOURS ?? 6) * 3600_000 },
  notify: { run: () => notifyReadySignals(), everyMs: Number(process.env.NOTIFY_EVERY_MIN ?? 1) * 60_000 },
} as const;

type JobName = keyof typeof JOBS;

async function runJob(name: JobName) {
  const started = new Date().toISOString();
  try {
    const result = await JOBS[name].run();
    console.log(`[${started}] job ${name} ok`, result);
  } catch (e: any) {
    console.error(`[${started}] job ${name} failed:`, e.message);
  }
}

async function main() {
  const redisUrl = process.env.REDIS_URL ?? 'redis://localhost:6379';
  const connection = new IORedis(redisUrl, { maxRetriesPerRequest: null, lazyConnect: true });
  try {
    await connection.connect();
    await connection.ping();
  } catch {
    console.warn('Redis unreachable — falling back to in-process interval scheduler (jobs still run).');
    for (const name of Object.keys(JOBS) as JobName[]) {
      await runJob(name);
      setInterval(() => runJob(name), JOBS[name].everyMs);
    }
    return;
  }

  const queue = new Queue('platform-jobs', { connection });
  for (const name of Object.keys(JOBS) as JobName[]) {
    await queue.add(name, {}, { repeat: { every: JOBS[name].everyMs }, jobId: `repeat-${name}` });
  }
  new Worker('platform-jobs', async (job) => runJob(job.name as JobName), { connection });
  console.log('Worker started with BullMQ (news/calendar/notify repeatable jobs).');
  for (const name of Object.keys(JOBS) as JobName[]) await runJob(name);
}

main();
