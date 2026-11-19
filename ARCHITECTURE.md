# ARCHITECTURE — Crypto AI Signals Platform

> منصة SaaS مستقلة 100% — لا Claude API في التشغيل اليومي. ذكاء = Rules-Based ICT/SMC + تعلم إحصائي داخل سيرفراتنا.

## 1. نظرة عامة

```
                         ┌─────────────────────────────────────────────┐
                         │              المستخدم (متصفح)               │
                         └──────────────────┬──────────────────────────┘
                                            │ HTTPS / WSS
                         ┌──────────────────▼──────────────────────────┐
                         │  Frontend — Next.js 14 (Vercel)             │
                         │  Landing + Dashboard + Signals + News       │
                         │  TypeScript · Tailwind · Zustand · Charts   │
                         └──────────────────┬──────────────────────────┘
                                            │ REST + WebSocket
                         ┌──────────────────▼──────────────────────────┐
                         │  Backend API — NestJS (Railway/Render)      │
                         │  Auth · Signals · Subscriptions · Swagger   │
                         │  Prisma ORM · BullMQ Producer               │
                         └───┬───────────────┬───────────────┬─────────┘
                             │               │               │
              ┌──────────────▼───┐  ┌────────▼───────┐  ┌────▼──────────────┐
              │ PostgreSQL       │  │ Redis (Upstash)│  │ Stripe            │
              │ (Supabase)       │  │ Cache · Queues │  │ Free/Pro/VIP      │
              └──────────────▲───┘  └────────▲───────┘  └───────────────────┘
                             │               │
              ┌──────────────┴───┐  ┌────────┴────────────────────────────┐
              │ AI Engine        │  │ Worker Service (Node + BullMQ)      │
              │ Python FastAPI   │  │ Telegram Bot · Email · News Agent   │
              │ فحص كل 5 دقائق   │  │ متابعة نتائج الإشارات TP/SL        │
              └──────────────┬───┘  └─────────────────────────────────────┘
                             │
              ┌──────────────▼──────────────────────────────────────────┐
              │ Binance REST · CoinGecko · (Nansen/Coinversa اختياري)  │
              └─────────────────────────────────────────────────────────┘
```

## 2. الخدمات

| الخدمة | المسار | التقنية | النشر | المسؤولية |
|---|---|---|---|---|
| Frontend | `apps/web` | Next.js 14 App Router + TS + Tailwind + Zustand | Vercel | Landing، Auth UI، Dashboard، Signals، Coin Details، News، Pricing |
| Backend API | `apps/api` | NestJS + Prisma | Railway / Render | REST API، Auth (Email+Google)، إشارات، اشتراكات Stripe، Swagger، WebSocket |
| AI Engine | `services/ai-engine` | Python + FastAPI + Pandas + TA-Lib + Scikit-learn | Railway / VPS (Docker) | فحص السوق كل 5 دقائق، مؤشرات ICT، مسارات A–D، Score، Backtest، تعلم |
| Worker | `services/worker` | Node + BullMQ | Railway / VPS | تنبيهات Telegram/Email، أخبار، متابعة نتائج الإشارات |
| DB | — | PostgreSQL (Supabase) + Redis (Upstash) | Managed | بيانات + Cache/Queues |

كل خدمة لها `Dockerfile` مستقل (Phase 6) ويمكن تطويرها/نشرها دون لمس الباقي.

## 3. تدفق البيانات (دورة فحص واحدة)

1. **AI Engine** (مجدول كل 5 دقائق): يجلب شموعًا مغلقة 4H/1H/15m من Binance (Cache في Redis)، يحسب الهيكل والمناطق والـ Regime وسياق BTC.
2. يشغّل المسارات المفعّلة A–D من `config/strategies.json`، يحسب Score من 10، يطبّق الفلاتر.
3. يحفظ `analyses` دائمًا، و`signals` عند WATCH/READY. الانتقال إلى READY فقط يطلق تنبيهًا.
4. **API** يقرأ الإشارات ويبثّها عبر WebSocket للمستخدمين حسب خطتهم وقائمة مراقبتهم.
5. **Worker** يلتقط مهام التنبيه من BullMQ ويرسل Telegram/Email، ويتابع الأسعار لتحديث `signal_outcomes` (TP1→BE→TP2/SL).
6. **التعلم:** نتائج مغلقة تغذّي `strategy_stats` ونموذج Scikit-learn لضبط أوزان الـ Score (ضمن حدود، وبعد شروط الاعتماد).

## 4. مبادئ الكود

- **Clean Architecture + Modular:** كل مؤشر/استراتيجية في ملف مستقل. إضافة استراتيجية = ملف جديد يرث `BaseStrategy` + سطر في `strategies.json`.
- **عقد البيانات:** `prisma/schema.prisma` + `packages/shared-types` (أنواع TS مشتركة بين web و api).
- **الأسرار:** متغيرات بيئة فقط (`.env.example` يوثقها). لا مفاتيح في الكود.
- **الاختبار:** Unit Tests للوظائف الحساسة (Swing, FVG, OB, Score, Risk) في كل خدمة.
- **التوثيق:** Swagger للـ API، و`docs/` للتشغيل والنشر.

## 5. حدود الخطط (تُفرض في API)

| الميزة | Free | Pro | VIP |
|---|---|---|---|
| إشارات READY | متأخرة + حد يومي | فورية | فورية + أولوية |
| تفاصيل التحليل والشارت | أساسي | كامل | كامل + لقطات POI |
| التنبيهات | In-App | + Email | + Telegram |
| Backtest / Journal | — | ✓ | ✓ + إحصاءات متقدمة |

> ⚠️ المنصة أداة تحليل تعليمية، ليست نصيحة مالية ولا تنفّذ صفقات نيابة عن المستخدم في الإطلاق.
