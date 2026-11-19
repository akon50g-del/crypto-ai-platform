'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import RequireAuth from '@/components/RequireAuth';
import SignalCard from '@/components/SignalCard';
import { api, SYMBOLS } from '@/lib/api';
import { useAuth } from '@/stores/auth';

function Inner() {
  const { user } = useAuth();
  const [signals, setSignals] = useState<any[]>([]);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    api('/signals?status=READY').then((d) => setSignals(d.signals)).catch((e) => setErr(e.message));
    api('/users/me/watchlist').then(setWatchlist).catch(() => {});
    api('/stats/strategies').then(setStats).catch(() => {});
  }, []);

  const watched = watchlist.map((w) => w.symbol);
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-extrabold">مرحبًا{user?.name ? `، ${user.name}` : ''}</h1>
        <span className="badge bg-accent/15 text-accent border border-accent/40">خطة {user?.planTier}</span>
      </div>
      {user?.planTier === 'FREE' && (
        <div className="card border-accent/40 text-sm">
          أنت على الخطة المجانية: الإشارات متأخرة 60 دقيقة وبحد 3 يوميًا.{' '}
          <Link href="/pricing" className="text-accent font-semibold">رقِّ إلى Pro للإشارات الفورية</Link>
        </div>
      )}
      <section>
        <h2 className="font-bold text-lg mb-3">عملاتي المفضلة</h2>
        <div className="flex gap-2 flex-wrap">
          {SYMBOLS.map((s) => (
            <Link key={s} href={`/coin/${s}`} className={`badge border ${watched.includes(s) ? 'bg-accent/15 text-accent border-accent/40' : 'bg-white/5 text-white/60 border-line'}`}>{s.replace('USDT', '')}</Link>
          ))}
        </div>
      </section>
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-lg">أحدث التوصيات الجاهزة (READY)</h2>
          <Link href="/signals" className="text-accent text-sm">الكل ←</Link>
        </div>
        {err && <p className="text-down text-sm">{err}</p>}
        {signals.length === 0
          ? <p className="card text-white/60">لا توجد توصيات جاهزة الآن — المحرك يفحص كل 5 دقائق ولا يفرض صفقات. جرّب صفحة عملة لرؤية التحليل الحالي.</p>
          : <div className="grid md:grid-cols-2 gap-4">{signals.slice(0, 4).map((s) => <SignalCard key={s.id} s={s} />)}</div>}
      </section>
      {stats && (
        <section>
          <h2 className="font-bold text-lg mb-3">أداء المسارات (صفقات مغلقة)</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {['A', 'B', 'C', 'D'].map((c) => {
              const st = stats.by_strategy?.[c];
              return (
                <div key={c} className="card text-sm">
                  <b>مسار {c}</b>
                  {st ? <p className="text-white/60 mt-1">صفقات {st.trades} · فوز {st.win_rate_pct}% · PF {st.profit_factor ?? '—'} · Net {st.net_r}R</p>
                      : <p className="text-white/40 mt-1">لا صفقات مغلقة بعد</p>}
                </div>
              );
            })}
          </div>
          <p className="text-white/40 text-xs mt-2">{stats.acceptance_rule}</p>
        </section>
      )}
    </div>
  );
}

export default function Page() {
  return <RequireAuth><Inner /></RequireAuth>;
}
