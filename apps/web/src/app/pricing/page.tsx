'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuth } from '@/stores/auth';

export default function Pricing() {
  const [plans, setPlans] = useState<any[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [msg, setMsg] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    api('/subscriptions/plans').then((d) => { setPlans(d.plans); setEnabled(d.payments_enabled); }).catch(() => {});
  }, []);

  async function upgrade(plan: string) {
    if (!user) return;
    try {
      const d = await api('/subscriptions/checkout', { method: 'POST', body: JSON.stringify({ plan }) });
      if (d.checkout_url) window.location.href = d.checkout_url;
    } catch (e: any) {
      setMsg(e.message?.includes('not enabled') ? 'الدفع غير مفعّل بعد — سيُتاح قريبًا. خطتك الحالية كما هي.' : e.message);
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-extrabold text-center">الأسعار</h1>
      {!enabled && <p className="text-center text-accent text-sm mt-2">الدفع عبر Stripe مهيأ في الكود وسيُفعَّل قريبًا.</p>}
      {msg && <p className="card text-center mt-4 text-accent">{msg}</p>}
      <div className="grid md:grid-cols-3 gap-4 mt-6">
        {plans.map((p) => (
          <div key={p.tier} className={`card ${p.tier === 'PRO' ? 'border-accent/60' : ''}`}>
            <h3 className="font-bold text-xl">{p.tier}</h3>
            <p className="text-3xl font-extrabold mt-2">${p.price_usd_month}<span className="text-sm text-white/50">/شهر</span></p>
            <ul className="text-white/60 text-sm mt-3 space-y-1">{p.features.map((f: string) => <li key={f}>✓ {f}</li>)}</ul>
            {user
              ? (user.planTier === p.tier
                ? <span className="btn btn-ghost w-full mt-4">خطتك الحالية</span>
                : <button onClick={() => upgrade(p.tier)} className="btn btn-primary w-full mt-4">الترقية إلى {p.tier}</button>)
              : <Link href="/register" className="btn btn-primary w-full mt-4">ابدأ مع {p.tier}</Link>}
          </div>
        ))}
      </div>
    </div>
  );
}
