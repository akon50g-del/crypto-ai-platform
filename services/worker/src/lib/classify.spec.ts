import { classifyImpact, extractSymbols, isBlackout, sentimentScore } from './classify';

describe('classifyImpact', () => {
  it('flags macro events HIGH', () => {
    expect(classifyImpact('US CPI inflation comes in hotter than expected')).toBe('HIGH');
    expect(classifyImpact('Fed signals rate cut after FOMC meeting')).toBe('HIGH');
    expect(classifyImpact('Bitcoin ETF approval sparks rally')).toBe('HIGH');
  });
  it('defaults MEDIUM and LOW for guides', () => {
    expect(classifyImpact('Ethereum upgrade scheduled for next month')).toBe('MEDIUM');
    expect(classifyImpact('How to buy Bitcoin: a beginner guide')).toBe('LOW');
  });
});

describe('extractSymbols / sentiment', () => {
  it('maps mentions to approved symbols only', () => {
    expect(extractSymbols('Bitcoin and Ethereum rally as Solana lags')).toEqual(
      expect.arrayContaining(['BTCUSDT', 'ETHUSDT', 'SOLUSDT']),
    );
    expect(extractSymbols('Cardano update')).toEqual([]);
  });
  it('scores sentiment direction', () => {
    expect(sentimentScore('Bitcoin surge to record high')).toBeGreaterThan(0);
    expect(sentimentScore('Exchange hack triggers selloff')).toBeLessThan(0);
  });
});

describe('isBlackout', () => {
  const now = new Date('2026-11-19T12:00:00Z');
  it('blocks ±30 min around HIGH events only', () => {
    expect(isBlackout([{ scheduledAt: new Date('2026-11-19T12:20:00Z'), impact: 'HIGH' }], now)).toBe(true);
    expect(isBlackout([{ scheduledAt: new Date('2026-11-19T13:00:00Z'), impact: 'HIGH' }], now)).toBe(false);
    expect(isBlackout([{ scheduledAt: new Date('2026-11-19T12:10:00Z'), impact: 'MEDIUM' }], now)).toBe(false);
  });
});
