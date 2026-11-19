'use client';
import { useCallback, useEffect, useState } from 'react';
import RequireAuth from '@/components/RequireAuth';
import { api, fmt, SYMBOLS } from '@/lib/api';

function Inner() {
  const [rows, setRows] = useState<any[]>([]);
  const [form, setForm] = useState<any>({ symbol: 'BTCUSDT', side: 'LONG', entryPrice: '', stopLoss: '', exitPrice: '', quantity: '', fees: '', reason: '' });
  const [err, setErr] = useState('');
  const load = useCallback(() => { api('/journal').then(setRows).catch((e) => setErr(e.message)); }, []);
  useEffect(() => { load(); }, [load]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api('/journal', {
        method: 'POST',
        body: JSON.stringify({
          symbol: form.symbol, side: form.side,
          entryPrice: +form.entryPrice,
          stopLoss: form.stopLoss ? +form.stopLoss : undefined,
          exitPrice: form.exitPrice ? +form.exitPrice : undefined,
          quantity: form.quantity ? +form.quantity : undefined,
          fees: form.fees ? +form.fees : undefined,
          reason: form.reason || undefined,
          closedAt: form.exitPrice ? new Date().toISOString() : undefined,
        }),
      });
      load();
    } catch (e: any) { setErr(e.message); }
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold">سجل الصفقات</h1>
      <p className="text-white/50 text-sm">سجّل القيم الفعلية فقط (سعر الخروج والحجم والرسوم) — الأرقام المفترضة تُفسد التحليل لاحقًا.</p>
      <form onSubmit={submit} className="card grid grid-cols-2 md:grid-cols-4 gap-3">
        <div><label className="label">العملة</label>
          <select className="input" value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>
            {SYMBOLS.map((s) => <option key={s} value={s}>{s}</option>)}</select></div>
        <div><label className="label">الاتجاه</label>
          <select className="input" value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value })}>
            <option>LONG</option><option>SHORT</option></select></div>
        <div><label className="label">سعر الدخول</label>
          <input className="input" type="number" step="any" required value={form.entryPrice} onChange={(e) => setForm({ ...form, entryPrice: e.target.value })} /></div>
        <div><label className="label">الوقف</label>
          <input className="input" type="number" step="any" value={form.stopLoss} onChange={(e) => setForm({ ...form, stopLoss: e.target.value })} /></div>
        <div><label className="label">سعر الخروج الفعلي</label>
          <input className="input" type="number" step="any" value={form.exitPrice} onChange={(e) => setForm({ ...form, exitPrice: e.target.value })} /></div>
        <div><label className="label">الحجم الفعلي</label>
          <input className="input" type="number" step="any" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} /></div>
        <div><label className="label">الرسوم</label>
          <input className="input" type="number" step="any" value={form.fees} onChange={(e) => setForm({ ...form, fees: e.target.value })} /></div>
        <div><label className="label">سبب الدخول</label>
          <input className="input" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} /></div>
        <button className="btn btn-primary col-span-2 md:col-span-4">إضافة للسجل</button>
      </form>
      {err && <p className="text-down text-sm">{err}</p>}
      {rows.length === 0 ? <p className="card text-white/60">لا صفقات مسجلة بعد.</p> : (
        <div className="space-y-2">
          {rows.map((r) => (
            <div key={r.id} className="card text-sm flex justify-between gap-2 flex-wrap">
              <span><b>{r.symbol}</b> {r.side} · دخول {fmt(r.entryPrice, 4)}{r.exitPrice ? ` · خروج ${fmt(r.exitPrice, 4)}` : ' · مفتوحة'}</span>
              <span className="text-white/50">{new Date(r.openedAt).toLocaleDateString('ar-EG')}{r.reason ? ` · ${r.reason}` : ''}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Page() {
  return <RequireAuth><Inner /></RequireAuth>;
}
