# دليل النشر — Crypto AI Signals Platform

## الخيار 1: VPS واحد (Docker Compose) — الأبسط والأرخص
متطلبات: VPS ‏(2 vCPU / 4GB RAM يكفي للبداية)، Docker + Compose، دومين اختياري.

```bash
git clone <repo> crypto-ai-platform && cd crypto-ai-platform
cp .env.example .env
# عدّل .env: POSTGRES_PASSWORD، JWT_SECRET، AI_ENGINE_INTERNAL_TOKEN، روابط عامة
docker compose up --build -d
docker compose ps
```

- الموقع: `http://<server>:3000` · API: `:4000/docs` · المحرك: `:8000/docs`
- أول تشغيل: الـ API ينفّذ `prisma db push` تلقائيًا (مخطط PostgreSQL الرسمي من الجذر).
- ازرع بيانات أولية: `docker compose exec api npm run db:seed`
- HTTPS: ضع Caddy أو Nginx أمام المنفذين 3000/4000 (مثال Caddy):

```
your-domain.com { reverse_proxy localhost:3000 }
api.your-domain.com { reverse_proxy localhost:4000 }
```
ثم حدّث `NEXT_PUBLIC_API_URL=https://api.your-domain.com` و`FRONTEND_URL=https://your-domain.com` وأعد البناء.

## الخيار 2: Vercel + Railway/Render (مُقسّم)
- **Frontend ‏(Vercel):** اربط `apps/web` كمشروع، اضبط `NEXT_PUBLIC_API_URL` و`NEXT_PUBLIC_WS_URL` على رابط الـ API العام.
- **API + Worker + Engine ‏(Railway/Render):** كل خدمة من Dockerfile الخاص بها (سياق البناء للـ API والـ Worker = جذر المشروع).
- **قاعدة البيانات:** Supabase ‏(PostgreSQL) — ضع `DATABASE_URL` ‏(و`DIRECT_URL` للترحيلات) في الـ API والـ Worker والمحرك.
- **Redis:** Upstash — ضع `REDIS_URL` في الـ Worker.

## تفعيل الميزات الاختيارية
| الميزة | المفاتيح | الأثر بدونها |
|---|---|---|
| Google Login | `GOOGLE_CLIENT_ID/SECRET` | زر Google لا يعمل، Email يعمل |
| Stripe | `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_PRICE_PRO/VIP` | checkout يرجع 503، الخطط تُعرض فقط |
| Telegram | `TELEGRAM_BOT_TOKEN` ‏(من @BotFather) | التنبيهات dry-run تُسجَّل فقط |
| Email | `SMTP_HOST/PORT/USER/PASS` | التنبيهات dry-run تُسجَّل فقط |

Stripe Webhook: وجّهه إلى `https://<api>/subscriptions/webhook` لأحداث `checkout.session.completed` و`customer.subscription.deleted`.

## التشغيل المحلي بدون Docker (تطوير)
كل خدمة تعمل وحدها بـ SQLite:
```bash
# 1) المحرك
cd services/ai-engine && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000
# 2) API
cd apps/api && cp .env.example .env && npm install && npx prisma generate && npx prisma db push && npm run db:seed && npm run dev
# 3) Worker (مهام منفصلة بدون Redis)
cd services/worker && cp .env.example .env && npm install && npx prisma generate && npm run job:news
# 4) الواجهة
cd apps/web && cp .env.example .env.local && npm install && npm run dev
```

## نسخ احتياطي
`docker compose exec postgres pg_dump -U crypto crypto_ai > backup.sql` — جدولها يوميًا ‏(cron) واحفظها خارج السيرفر.

## ملاحظات إنتاجية
- لا تنفّذ المنصة صفقات آليًا — إشارات وتنبيهات فقط.
- راقب `GET /health` لكل خدمة، وسجلات المحرك ‏(`engine_runs`) لاكتشاف أي فحص فاشل.
- Binance: إن حُجب `api.binance.com` في بلد السيرفر، اترك الافتراضي `data-api.binance.vision`.
