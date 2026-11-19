# خطة النشر على Railway + Vercel — Crypto AI Signals Platform

> الهدف: رابط عام للموقع + دخول تجريبي، بأقل عدد حسابات. كل الأسرار تُولّد وتُضبط أثناء النشر، لا تُحفظ في Git.

## المعمارية على السحابة

| الخدمة | المنصة | المصدر | ملاحظات |
|---|---|---|---|
| Web (Next.js) | Vercel | `apps/web` | Root Directory = `apps/web`، ملف `vercel.json` جاهز |
| API (NestJS) | Railway | Dockerfile `apps/api/Dockerfile` | Root = جذر الريبو، Config = `deploy/railway/api.toml`، منفذ 4000، Health `/health` |
| AI Engine (FastAPI) | Railway | Dockerfile `services/ai-engine/Dockerfile` | Root = `services/ai-engine`، Config = `deploy/railway/engine.toml`، خاص بدون دومين عام |
| Worker (BullMQ) | Railway | Dockerfile `services/worker/Dockerfile` | Root = جذر الريبو، Config = `deploy/railway/worker.toml`، بدون منفذ عام |
| PostgreSQL | Railway (Plugin) | — | يوفّر `DATABASE_URL` تلقائيًا — بديل أبسط من Supabase لحساب واحد |
| Redis | Railway (Plugin) | — | يوفّر `REDIS_URL` للـ Worker — بديل أبسط من Upstash |

> اختيار Railway DB/Redis بدل Supabase/Upstash يقلّل الحسابات من 4 إلى 2 (GitHub + Railway، وVercel يدخل بـ GitHub). يمكن التبديل لاحقًا بتغيير `DATABASE_URL`/`REDIS_URL` فقط.

## ترتيب التنفيذ

1. **GitHub:** إنشاء ريبو خاص `crypto-ai-platform` ودفع الكود (`.gitignore` يستبعد `.env.*` ما عدا `.env.example`).
2. **Railway:** مشروع جديد من الريبو + إضافة PostgreSQL وRedis + 3 خدمات (API/Engine/Worker) بالإعدادات أعلاه.
3. **متغيرات البيئة** (تُولّد أسرار قوية وقتها):
   - API: `DATABASE_URL` (من Railway)، `JWT_SECRET`، `AI_ENGINE_INTERNAL_TOKEN`، `AI_ENGINE_URL` (رابط Engine الداخلي)، `FRONTEND_URL` (رابط Vercel بعد إنشائه)، `BINANCE_BASE_URL=https://data-api.binance.vision`، واختياريًا Google/Stripe.
   - Engine: `DATABASE_URL`، `AI_ENGINE_INTERNAL_TOKEN` (نفس قيمة API)، `BINANCE_BASE_URL`.
   - Worker: `DATABASE_URL`، `REDIS_URL`، واختياريًا `TELEGRAM_BOT_TOKEN` وSMTP (بدونها التنبيهات dry-run بصدق).
   - Web (Vercel): `NEXT_PUBLIC_API_URL` و`NEXT_PUBLIC_WS_URL` = رابط API العام على Railway.
4. **أول إقلاع:** API ينفّذ `prisma db push` تلقائيًا من CMD في Dockerfile، ثم زرع البيانات: `npm run db:seed` (دخول تجريبي PRO).
5. **Vercel:** مشروع من نفس الريبو، Root = `apps/web`، ثم تحديث `FRONTEND_URL` في API وإعادة نشر API.
6. **تحقق:** `GET /health` للـ API والمحرك، فتح رابط Vercel، تسجيل دخول تجريبي، ظهور الإشارات بعد أول فحص (كل 5 دقائق).

## حدود يجب معرفتها
- Railway قد يطلب وسيلة دفع بعد فترة التجربة/الائتمان المجاني — القرار والبطاقة للمستخدم وحده.
- بدون مفاتيح Google/Stripe/Telegram/SMTP: الدخول بالإيميل يعمل، الدفع يرجع 503، التنبيهات تُسجّل فقط.
- المنصة إشارات وتنبيهات فقط — لا تنفيذ صفقات آليًا. ليست نصيحة مالية.
- التشغيل الأول بمرحلة "تنبيهات فقط" وجمع ≥100 صفقة مغلقة لكل مسار قبل اعتماد أي مسار أو تفعيل الدفع.
