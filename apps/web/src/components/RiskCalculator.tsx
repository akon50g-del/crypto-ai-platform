'use client';
import { useMemo, useState } from 'react';
import { fmt } from '@/lib/api';
import { positionSize } from '@/lib/risk';

export default function RiskCalculator({ entry, sl, tp1, tp2 }: { entry: number; sl: number; tp1: number; tp2: number }) {
  const [balance, setBalance] = useState(1000);
  const [riskPct, setRiskPct] = useState(1);
  const [leverage, setLeverage] = useState(3);
  const result = useMemo(() => positionSize(balance, riskPct, entry, sl, [tp1, tp2], leverage),
    [balance, riskPct, entry, sl, tp1, tp2, leverage]);

  return (
    <div className="card">
      <h3 className="font-bold">حاسبة حجم الصفقة</h3>
      <div className="grid grid-cols-3 gap-2 mt-3">
        <div><label className="label">الرصيد ($)</label>
          <input className="input" type="number" value={balance} onChange={(e) => setBalance(+e.target.value)} /></div>
        <div><label className="label">المخاطرة %</label>
          <input className="input" type="number" step="0.1" value={riskPct} onChange={(e) => setRiskPct(+e.target.value)} /></div>
        <div><label className="label">الرافعة</label>
          <input className="input" type="number" value={leverage} onChange={(e) => setLeverage(+e.target.value)} /></div>
      </div>
      {result && (
        <div className="text-sm mt-3 space-y-1 text-white/70">
          <p>الاتجاه: <b>{result.side}</b> · مبلغ المخاطرة: <b>${fmt(result.riskAmount)}</b> · المسافة للوقف: {fmt(result.slDistancePct)}%</p>
          <p>الكمية: <b>{fmt(result.qty, 6)}</b> · القيمة الاسمية: ${fmt(result.notional)} · الهامش: ${fmt(result.margin)}</p>
          {result.targets.map((t, i) => (
            <p key={i}>TP{i + 1} عند {fmt(t.price)}: ربح تقريبي ${fmt(t.pnl)} (RR {fmt(t.rr)})</p>
          ))}
          <p className="text-white/40 text-xs">قبل الرسوم والانزلاق — راجع منصة التنفيذ. Isolated ورافعة منخفضة 2–3x، والوقف مربوط دائمًا.</p>
        </div>
      )}
    </div>
  );
}
