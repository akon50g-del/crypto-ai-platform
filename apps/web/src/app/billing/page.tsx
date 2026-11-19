'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import RequireAuth from '@/components/RequireAuth';
import { api } from '@/lib/api';

function Inner() {
  const [sub, setSub] = useState<any>(null);
  useEffect(() => { api('/subscriptions/me').then(setSub).catch(() => {}); }, []);
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold">الاشتراك</h1>
      <div className="card">
        <p>الخطة الحالية: <b className="text-accent">{sub?.planTier ?? 'FREE'}</b> · الحالة: {sub?.status ?? 'ACTIVE'}</p>
        {sub?.currentPeriodEnd && <p className="text-white/50 text-sm mt-1">حتى {new Date(sub.currentPeriodEnd).toLocaleDateString('ar-EG')}</p>}
        <Link href="/pricing" className="btn btn-primary mt-4">عرض الخطط والترقية</Link>
        <p className="text-white/40 text-xs mt-3">الدفع عبر Stripe مهيأ في الكود وسيُفعَّل عند ضبط المفاتيح في الإنتاج.</p>
      </div>
      {sub?.payments?.length > 0 && (
        <div className="card">
          <h3 className="font-bold mb-2">المدفوعات</h3>
          {sub.payments.map((p: any) => (
            <p key={p.id} className="text-sm text-white/60">${(p.amountCents / 100).toFixed(2)} · {p.status} · {new Date(p.createdAt).toLocaleDateString('ar-EG')}</p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Page() {
  return <RequireAuth><Inner /></RequireAuth>;
}
