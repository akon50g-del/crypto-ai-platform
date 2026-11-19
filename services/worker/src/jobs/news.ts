import Parser from 'rss-parser';
import { classifyImpact, extractSymbols, sentimentScore } from '../lib/classify';
import { prisma } from '../lib/prisma';

const FEEDS = [
  { source: 'coindesk', url: 'https://www.coindesk.com/arc/outboundfeeds/rss/' },
  { source: 'cointelegraph', url: 'https://cointelegraph.com/rss' },
  { source: 'decrypt', url: 'https://decrypt.co/feed' },
];

export async function fetchNews(): Promise<{ inserted: number; skipped: number; errors: string[] }> {
  const parser = new Parser({ timeout: 20_000 });
  let inserted = 0, skipped = 0;
  const errors: string[] = [];
  for (const feed of FEEDS) {
    try {
      const parsed = await parser.parseURL(feed.url);
      for (const item of parsed.items.slice(0, 30)) {
        if (!item.title || !item.link) { skipped++; continue; }
        const exists = await prisma.newsItem.findUnique({ where: { url: item.link } });
        if (exists) { skipped++; continue; }
        await prisma.newsItem.create({
          data: {
            source: feed.source,
            title: item.title,
            url: item.link,
            symbols: extractSymbols(item.title),
            impact: classifyImpact(item.title),
            sentiment: sentimentScore(item.title),
            publishedAt: item.isoDate ? new Date(item.isoDate) : new Date(),
          },
        });
        inserted++;
      }
    } catch (e: any) {
      errors.push(`${feed.source}: ${e.message}`);
    }
  }
  return { inserted, skipped, errors };
}
