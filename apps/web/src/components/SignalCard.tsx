'use client';
import Link from 'next/link';
import { fmt } from '@/lib/api';

export function ScoreBadge({ score, grade }: { score: number; grade?: string }) {
  const color = score >= 8 ? 'bg-up/20 text-up border-up/50' : score >= 7 ? 'bg-accent/15 text-accent border-accent/40' : 'bg-white/10 text-white/60 border-line';
  return <span className={`badge border ${color}`}>Score {score}/10{grade ? ` · ${grade}` : ''}</span>;
}

export default function SignalCard({ s }: { s: any }) {
  const long = s.side === 'LONG';
  return (
    <Link href={`/coin/${s.symbol}`} className="card block hover:border-accent/50 transition">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="font-bold">{s.symbol}</span>
          <span className={`badge ${long ? 'bg-up/20 text-up' : 'bg-down/20 text-down'}`}>{s.side}</span>
          <span className="badge bg-white/10 text-white/70">مسار {s.strategy}</span>
          <span className="badge bg-white/10 text-white/70">{s.status}</span>
        </div>
        <ScoreBadge score={s.score} grade={s.grade} />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-sm">
        <div><div className="text-white/50 text-xs">الدخول</div>{fmt(s.entry_zone?.[0])} – {fmt(s.entry_zone?.[1])}</div>
        <div><div className="text-white/50 text-xs">وقف الخسارة</div><span className="text-down">{fmt(s.stop_loss)}</span></div>
        <div><div className="text-white/50 text-xs">TP1 (RR {fmt(s.rr_tp1)})</div><span className="text-up">{fmt(s.tp1)}</span></div>
        <div><div className="text-white/50 text-xs">TP2 (RR {fmt(s.rr_tp2)})</div><span className="text-up">{fmt(s.tp2)}</span></div>
      </div>
      {s.reason_ar && <p className="text-white/60 text-sm mt-2">{s.reason_ar}</p>}
      {s.outcome?.result && s.outcome.result !== 'OPEN' && (
        <p className="text-sm mt-1">النتيجة: <b>{s.outcome.result}</b>{s.outcome.realized_r != null ? ` (${fmt(s.outcome.realized_r)}R)` : ''}</p>
      )}
      <p className="text-white/40 text-xs mt-2">{s.created_at ? new Date(s.created_at).toLocaleString('ar-EG') : ''}</p>
    </Link>
  );
}
