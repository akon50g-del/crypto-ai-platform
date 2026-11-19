'use client';
import { useEffect, useState } from 'react';
import RequireAuth from '@/components/RequireAuth';
import { api, SYMBOLS } from '@/lib/api';

function Inner() {
  const [prefs, setPrefs] = useState<any>({ defaultBalance: 1000, riskPerTradePct: 1, leverage: 3, minScoreAlert: 7 });
  const [watch, setWatch] = useState<string[]>([]);
  const [channels, setChannels] = useState<any>({ EMAIL: false, TELEGRAM: false, telegramChatId: '' });
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api('/users/me/preferences').then((d) => d && setPrefs(d)).catch(() => {});
    api('/users/me/watchlist').then((d) => setWatch(d.map((w: any) => w.symbol))).catch(() => {});
    api('/users/me/notification-preferences').then((d) => {
      const next: any = { EMAIL: false, TELEGRAM: false, telegramChatId: '' };
      for (const p of d) { next[p.channel] = p.enabled; if (p.telegramChatId) next.telegramChatId = p.telegramChatId; }
      setChannels(next);
    }).catch(() => {});
  }, []);

  async function savePrefs() {
    await api('/users/me/preferences', { method: 'PUT', body: JSON.stringify({
      defaultBalance: +prefs.defaultBalance, riskPerTradePct: +prefs.riskPerTradePct,
      leverage: +prefs.leverage, minScoreAlert: +prefs.minScoreAlert, strategies: ['A', 'B', 'C', 'D'],
    })});
    setMsg('تم حفظ التفضيلات');
  }

  async function toggleWatch(symbol: string) {
    if (watch.includes(symbol)) {
      await api(`/users/me/watchlist/${symbol}`, { method: 'DELETE' });
      setWatch(watch.filter((s) => s !== symbol));
    } else {
      await api('/users/me/watchlist', { method: 'POST', body: JSON.stringify({ symbol }) });
      setWatch([...watch, symbol]);
    }
  }

  async function saveChannel(channel: string, enabled: boolean) {
    const next = { ...channels, [channel]: enabled };
    setChannels(next);
    await api('/users/me/notification-preferences', { method: 'PUT', body: JSON.stringify({
      channel, enabled, telegramChatId: channel === 'TELEGRAM' ? next.telegramChatId || undefined : undefined,
    })});
    setMsg('تم حفظ قنوات التنبيه');
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold">الإعدادات</h1>
      {msg && <p className="card text-up text-sm">{msg}</p>}
      <div className="card space-y-3">
        <h3 className="font-bold">إدارة المخاطر الافتراضية</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div><label className="label">الرصيد ($)</label>
            <input className="input" type="number" value={prefs.defaultBalance} onChange={(e) => setPrefs({ ...prefs, defaultBalance: e.target.value })} /></div>
          <div><label className="label">المخاطرة لكل صفقة %</label>
            <input className="input" type="number" step="0.1" value={prefs.riskPerTradePct} onChange={(e) => setPrefs({ ...prefs, riskPerTradePct: e.target.value })} /></div>
          <div><label className="label">الرافعة</label>
            <input className="input" type="number" value={prefs.leverage} onChange={(e) => setPrefs({ ...prefs, leverage: e.target.value })} /></div>
          <div><label className="label">أدنى Score للتنبيه</label>
            <input className="input" type="number" min={5} max={10} value={prefs.minScoreAlert} onChange={(e) => setPrefs({ ...prefs, minScoreAlert: e.target.value })} /></div>
        </div>
        <button onClick={savePrefs} className="btn btn-primary">حفظ</button>
        <p className="text-white/40 text-xs">القاعدة الافتراضية: مخاطرة 1% لكل صفقة وحد يومي 2% — لا ترفعها لزيادة عدد الفرص.</p>
      </div>
      <div className="card">
        <h3 className="font-bold mb-3">العملات المفضلة</h3>
        <div className="flex gap-2 flex-wrap">
          {SYMBOLS.map((s) => (
            <button key={s} onClick={() => toggleWatch(s)} className={`badge border ${watch.includes(s) ? 'bg-accent/15 text-accent border-accent/40' : 'bg-white/5 text-white/60 border-line'}`}>{s.replace('USDT', '')}</button>
          ))}
        </div>
      </div>
      <div className="card space-y-3">
        <h3 className="font-bold">طريقة التنبيه</h3>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={!!channels.EMAIL} onChange={(e) => saveChannel('EMAIL', e.target.checked)} /> البريد الإلكتروني
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={!!channels.TELEGRAM} onChange={(e) => saveChannel('TELEGRAM', e.target.checked)} /> Telegram
        </label>
        <div>
          <label className="label">Telegram Chat ID (اختياري — يفعّل البوت في Phase 5)</label>
          <input className="input" value={channels.telegramChatId} onChange={(e) => setChannels({ ...channels, telegramChatId: e.target.value })}
            onBlur={() => channels.TELEGRAM && saveChannel('TELEGRAM', true)} />
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return <RequireAuth><Inner /></RequireAuth>;
}
