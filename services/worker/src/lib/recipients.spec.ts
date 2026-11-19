import { selectRecipients, type SignalLike, type UserLike } from './recipients';

const now = new Date('2026-11-19T12:00:00Z');
const freshSignal: SignalLike = {
  id: 's1', symbol: 'BTCUSDT', strategy: 'A', score: 8, status: 'READY',
  createdAt: new Date('2026-11-19T11:55:00Z'),
};
const user = (over: Partial<UserLike> = {}): UserLike => ({
  id: 'u1', email: 'a@b.com', planTier: 'PRO', minScoreAlert: 7,
  strategies: ['A', 'B', 'C', 'D'], watchlist: [],
  channels: [{ channel: 'EMAIL', enabled: true }, { channel: 'TELEGRAM', enabled: true, telegramChatId: '123' }],
  ...over,
});

describe('selectRecipients', () => {
  it('PRO user gets both channels immediately', () => {
    const r = selectRecipients(freshSignal, [user()], new Set(), now);
    expect(r.map((x) => x.channel).sort()).toEqual(['EMAIL', 'TELEGRAM']);
  });
  it('FREE user waits 60 minutes', () => {
    expect(selectRecipients(freshSignal, [user({ planTier: 'FREE' })], new Set(), now)).toEqual([]);
    const later = new Date('2026-11-19T13:00:00Z');
    expect(selectRecipients(freshSignal, [user({ planTier: 'FREE' })], new Set(), later).length).toBe(2);
  });
  it('respects min score, strategy filter, watchlist', () => {
    expect(selectRecipients(freshSignal, [user({ minScoreAlert: 9 })], new Set(), now)).toEqual([]);
    expect(selectRecipients(freshSignal, [user({ strategies: ['B'] })], new Set(), now)).toEqual([]);
    expect(selectRecipients(freshSignal, [user({ watchlist: ['ETHUSDT'] })], new Set(), now)).toEqual([]);
    expect(selectRecipients(freshSignal, [user({ watchlist: ['BTCUSDT'] })], new Set(), now).length).toBe(2);
  });
  it('dedupes already-SENT and skips disabled/missing telegram', () => {
    const r = selectRecipients(freshSignal, [user()], new Set(['u1:EMAIL']), now);
    expect(r.map((x) => x.channel)).toEqual(['TELEGRAM']);
    const noTg = user({ channels: [{ channel: 'TELEGRAM', enabled: true, telegramChatId: null }] });
    expect(selectRecipients(freshSignal, [noTg], new Set(), now)).toEqual([]);
  });
  it('ignores non-READY signals', () => {
    expect(selectRecipients({ ...freshSignal, status: 'WATCH' }, [user()], new Set(), now)).toEqual([]);
  });
});
