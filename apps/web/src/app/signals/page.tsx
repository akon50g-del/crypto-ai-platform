'use client';
import { useCallback, useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import RequireAuth from '@/components/RequireAuth';
import SignalCard from '@/components/SignalCard';
import { api, SYMBOLS, WS_URL } from '@/lib/api';

function Inner() {
  const [signals, setSignals] = useState<any[]>([]);
  const [status, setStatus] = useState('');
  const [strategy, setStrategy] = useState('');
  const [symbol, setSymbol] = useState('');
  const [live, setLive] = useState(false);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    try {
      const q = new URLSearchParams();
      if (status) q.set('status', status);
      if (strategy) q.set('strategy', strategy);
      if (symbol) q.set('symbol', symbol);
      const d = await api(`/signals?${q.toString()}`);
      setSignals(d.signals);
    } catch (e: any) { setErr(e.message); }
  }, [status, strategy, symbol]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const socket = io(WS_URL, { path: '/ws/signals', transports: ['websocket'] });
    socket.on('connect', () => setLive(true));
    socket.on('disconnect', () => setLive(false));
    socket.on('signal.ready', () => load());
    return () => { socket.disconnect(); };
  }, [load]);

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-extrabold">التوصيات الحية</h1>
        <span className={`badge border ${live ? 'bg-up/15 text-up border-up/40' : 'bg-white/10 text-white/50 border-line'}`}>
          {live ? '● متصل — تحديث فوري' : '○ غير متصل'}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 mt-4">
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">كل الحالات</option>
          <option value="READY">READY</option><option value="TRIGGERED">TRIGGERED</option>
          <option value="WATCH">WATCH</option><option value="CLOSED">CLOSED</option>
        </select>
        <select className="input" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
          <option value="">كل المسارات</option>
          {['A', 'B', 'C', 'D'].map((c) => <option key={c} value={c}>مسار {c}</option>)}
        </select>
        <select className="input" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
          <option value="">كل العملات</option>
          {SYMBOLS.map((s) => <option key={s} value={s}>{s.replace('USDT', '')}</option>)}
        </select>
      </div>
      {err && <p className="text-down text-sm mt-3">{err}</p>}
      {signals.length === 0
        ? <p className="card text-white/60 mt-4">لا توجد إشارات مطابقة. تذكّر: إشارات WATCH (Score 5–6) للمراقبة فقط، والتنفيذ عند 7 فأكثر.</p>
        : <div className="grid md:grid-cols-2 gap-4 mt-4">{signals.map((s) => <SignalCard key={s.id} s={s} />)}</div>}
    </div>
  );
}

export default function Page() {
  return <RequireAuth><Inner /></RequireAuth>;
}
