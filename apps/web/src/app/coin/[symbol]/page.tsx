'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import IctChart from '@/components/IctChart';
import RequireAuth from '@/components/RequireAuth';
import RiskCalculator from '@/components/RiskCalculator';
import SignalCard from '@/components/SignalCard';
import { api, fmt, SYMBOLS } from '@/lib/api';

function Inner({ symbol }: { symbol: string }) {
  const [tf, setTf] = useState('1h');
  const [candles, setCandles] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    api(`/coins/${symbol}/candles?tf=${tf}&limit=200`).then((d) => setCandles(d.candles)).catch((e) => setErr(e.message));
  }, [symbol, tf]);
  useEffect(() => {
    api(`/coins/${symbol}/analysis`).then(setAnalysis).catch(() => {});
    api(`/signals?symbol=${symbol}`).then((d) => setSignals(d.signals)).catch(() => {});
  }, [symbol]);

  const latest = signals[0];
  const a = analysis?.analysis;
  const lines = latest ? {
    entryLow: latest.entry_zone?.[0], entryHigh: latest.entry_zone?.[1],
    sl: latest.stop_loss, tp1: latest.tp1, tp2: latest.tp2,
  } : undefined;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-extrabold">{symbol.replace('USDT', '')}/USDT</h1>
        <div className="flex gap-1">
          {['15m', '1h', '4h', '1d'].map((t) => (
            <button key={t} onClick={() => setTf(t)} className={`badge border ${tf === t ? 'bg-accent/15 text-accent border-accent/40' : 'bg-white/5 text-white/60 border-line'}`}>{t}</button>
          ))}
        </div>
      </div>
      <div className="flex gap-2 flex-wrap">
        {SYMBOLS.map((s) => (
          <Link key={s} href={`/coin/${s}`} className={`badge border ${s === symbol ? 'bg-accent/15 text-accent border-accent/40' : 'bg-white/5 text-white/60 border-line'}`}>{s.replace('USDT', '')}</Link>
        ))}
      </div>
      {err && <p className="text-down text-sm">{err}</p>}
      <IctChart candles={candles} lines={lines} />
      <p className="text-white/40 text-xs">الشارت بتوقيت UTC وأسعاره من Binance. خطوط الدخول/الوقف/الأهداف من أحدث إشارة للمحرك إن وُجدت.</p>

      {a ? (
        <div className="card text-sm space-y-1">
          <h3 className="font-bold text-base">آخر تحليل ICT</h3>
          <p>السعر وقت التحليل: <b>{fmt(a.priceAtAnalysis, 4)}</b> ({a.priceSource}) · Bias ‏4H: <b>{a.bias}</b> · Regime: <b>{a.regime}</b></p>
          {analysis.analysis_locked
            ? <p className="text-accent">تفاصيل المناطق (FVG/OB/سيولة) متاحة لخطط Pro/VIP — <Link href="/pricing" className="underline">رقِّ خطتك</Link></p>
            : (<>
              <p>BSL فوق: {(a.structureJson?.bsl_above ?? []).map((x: number) => fmt(x)).join(' · ') || '—'}</p>
              <p>SSL تحت: {(a.structureJson?.ssl_below ?? []).map((x: number) => fmt(x)).join(' · ') || '—'}</p>
              <p>FVG مفتوحة: {(a.poiJson?.open_fvgs ?? []).length} · Order Blocks: {(a.poiJson?.order_blocks ?? []).length}</p>
              <p>سياق BTC ‏4H: <b>{a.btcContextJson?.btc_bias_4h ?? '—'}</b></p>
            </>)}
        </div>
      ) : <p className="card text-white/60 text-sm">لا يوجد تحليل محفوظ بعد — شغّل المحرك (POST /scan) أو انتظر دورة الفحص التالية.</p>}

      {latest && (
        <RiskCalculator
          entry={(latest.entry_zone[0] + latest.entry_zone[1]) / 2}
          sl={latest.stop_loss} tp1={latest.tp1} tp2={latest.tp2} />
      )}

      <section>
        <h2 className="font-bold text-lg mb-3">إشارات هذه العملة</h2>
        {signals.length === 0
          ? <p className="card text-white/60">لا إشارات حاليًا — لا دخول الآن. تابع مستويات BSL/SSL أعلاه لضبط تنبيهاتك.</p>
          : <div className="grid md:grid-cols-2 gap-4">{signals.map((s) => <SignalCard key={s.id} s={s} />)}</div>}
      </section>
    </div>
  );
}

export default function Page({ params }: { params: { symbol: string } }) {
  return <RequireAuth><Inner symbol={params.symbol.toUpperCase()} /></RequireAuth>;
}
