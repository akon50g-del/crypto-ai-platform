import Link from 'next/link';

const FEATURES = [
  { t: 'محرك ICT/SMC مستقل', d: 'يفحص 8 عملات سائلة كل 5 دقائق: هيكل السوق، FVG، Order Blocks، سحب سيولة، وOTE — بدون أي اعتماد خارجي.' },
  { t: 'Score موحد من 10', d: 'كل إشارة مُقيّمة بمعيار واحد شفاف. لا تنفيذ أقل من 7، ولا صفقات مفروضة لزيادة العدد.' },
  { t: 'خطة صفقة كاملة', d: 'منطقة دخول، وقف خلف أصل الحركة، هدفان عند سيولة فعلية، وحجم صفقة بمخاطرة 1% قابلة للضبط.' },
  { t: 'يتعلم من النتائج', d: 'كل توصية تُتتبع حتى TP/SL وتُقاس بـ R وProfit Factor لكل مسار — ولا يُعتمد مسار قبل 100 صفقة.' },
];

const STRATEGIES = [
  { c: 'A', t: 'ICT Continuation', d: 'استمرار مع اتجاه 4H من منطقة FVG/OB + OTE بعد MSS على 15m.' },
  { c: 'B', t: 'Liquidity Sweep Reversal', d: 'انعكاس بعد سحب BSL/SSL وإغلاق عائد + MSS — لا دخول بدون سحب.' },
  { c: 'C', t: 'Breakout Retest', d: 'كسر مع اتجاه EMA/ADX ثم إعادة اختبار ورفض.' },
  { c: 'D', t: 'Mean Reversion', d: 'ارتداد من حدود النطاق في سوق جانبي منخفض ADX فقط.' },
];

const PLANS = [
  { tier: 'FREE', price: 0, features: ['إشارات متأخرة 60 دقيقة', '3 إشارات يوميًا', 'تحليل أساسي'] },
  { tier: 'PRO', price: 19, features: ['إشارات فورية', 'تحليل كامل + شارت ICT', 'تنبيهات Email', 'سجل صفقات'] },
  { tier: 'VIP', price: 49, features: ['كل مزايا Pro', 'تنبيهات Telegram', 'إحصاءات متقدمة', 'أولوية الدعم'] },
];

export default function Landing() {
  return (
    <div className="space-y-14">
      <section className="text-center py-10">
        <p className="text-accent font-semibold">منصة تحليل ICT/SMC تعمل 24/7</p>
        <h1 className="text-4xl md:text-5xl font-extrabold mt-3 leading-tight">
          توصيات عملات رقمية<br />بمنطق مؤسسي، لا بعشوائية
        </h1>
        <p className="text-white/60 mt-4 max-w-2xl mx-auto">
          محرك ذكاء مستقل يفحص السوق كل 5 دقائق، يبني خطة صفقة كاملة بالدخول والوقف والأهداف،
          ويصلك إشعار عند كل إعداد مؤهل فقط (Score ≥ 7).
        </p>
        <div className="flex gap-3 justify-center mt-6 flex-wrap">
          <Link href="/register" className="btn btn-primary">ابدأ مجانًا</Link>
          <Link href="/pricing" className="btn btn-ghost">عرض الأسعار</Link>
        </div>
        <p className="text-white/40 text-sm mt-4">BTC · ETH · SOL · XRP · BNB · DOGE · LINK · AVAX</p>
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        {FEATURES.map((f) => (
          <div key={f.t} className="card"><h3 className="font-bold text-lg">{f.t}</h3><p className="text-white/60 mt-1">{f.d}</p></div>
        ))}
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">أربعة مسارات، سجل منفصل لكل مسار</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {STRATEGIES.map((s) => (
            <div key={s.c} className="card">
              <span className="badge bg-accent/15 text-accent border border-accent/40">مسار {s.c}</span>
              <h3 className="font-bold mt-2">{s.t}</h3><p className="text-white/60 text-sm mt-1">{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4 text-center">الاشتراكات</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {PLANS.map((p) => (
            <div key={p.tier} className={`card ${p.tier === 'PRO' ? 'border-accent/60' : ''}`}>
              <h3 className="font-bold text-xl">{p.tier}</h3>
              <p className="text-3xl font-extrabold mt-2">${p.price}<span className="text-sm text-white/50">/شهر</span></p>
              <ul className="text-white/60 text-sm mt-3 space-y-1">{p.features.map((f) => <li key={f}>✓ {f}</li>)}</ul>
              <Link href="/register" className="btn btn-primary w-full mt-4">اختر {p.tier}</Link>
            </div>
          ))}
        </div>
      </section>

      <section className="card text-center">
        <h2 className="text-xl font-bold">تنبيه مهم</h2>
        <p className="text-white/60 mt-2">المنصة أداة تحليل تعليمية ولا تنفّذ صفقات نيابة عنك. لا إشارة أقل من Score 7 تُعرض كصفقة جاهزة،
        والهدف النهائي لا يقل عن 1:2. قرار التنفيذ والمخاطرة مسؤوليتك دائمًا.</p>
      </section>
    </div>
  );
}
