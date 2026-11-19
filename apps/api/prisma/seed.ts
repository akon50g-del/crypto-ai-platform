import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT', 'DOGEUSDT', 'LINKUSDT', 'AVAXUSDT'];
  for (const symbol of symbols) {
    await prisma.symbol.upsert({
      where: { symbol }, update: {},
      create: { symbol, baseAsset: symbol.replace('USDT', '') },
    });
  }
  const passwordHash = await bcrypt.hash('demo-password-123', 12);
  await prisma.user.upsert({
    where: { email: 'demo@example.com' },
    update: {},
    create: {
      email: 'demo@example.com', passwordHash, name: 'Demo User', planTier: 'PRO',
      subscription: { create: { planTier: 'PRO', status: 'ACTIVE' } },
      preferences: { create: { strategies: ["A", "B", "C", "D"] } },
      watchlist: { create: [{ symbol: 'BTCUSDT' }, { symbol: 'ETHUSDT' }] },
    },
  });
  console.log('seeded: 8 symbols + demo@example.com / demo-password-123 (PRO)');
}

main().finally(() => prisma.$disconnect());
