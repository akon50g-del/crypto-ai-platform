# Backend API (NestJS + Prisma) — Phase 3 ✅

REST API + WebSocket للمنصة: Auth ‏(Email + Google)، توصيات مفلترة حسب الخطة، اشتراكات Stripe مهيأة، أخبار، جورنال، إحصاءات، وSwagger على `/docs`.

## الوحدات
```
src/
  auth/          register/login (bcrypt+JWT), Google OAuth (يُفعَّل بالمفاتيح), /auth/me
  signals/       /signals (تأخير+حد للـ FREE)، /signals/:id، /coins/:symbol/analysis، /coins/:symbol/candles
  users/         preferences, watchlist, notification-preferences, notifications
  subscriptions/ plans, checkout (Stripe — 503 حتى تُضبط المفاتيح), webhook, me
  news/          /news, /calendar
  journal/       CRUD سجل الصفقات (قيم فعلية فقط)
  stats/         /stats/strategies (PF/Expectancy/NetR لكل مسار)
  internal/      POST /internal/signals + /outcomes (للمحرك، X-Internal-Token) + WebSocket /ws/signals
  prisma/        PrismaService
prisma/
  schema.prisma            نسخة SQLite للتطوير المحلي (مولّدة من المخطط الرسمي)
  make-sqlite-schema.py    مولّد النسخة المحلية من ../../prisma/schema.prisma
  seed.ts                  8 رموز + demo@example.com (PRO)
```

## التشغيل المحلي (SQLite — بدون أي إعداد خارجي)
```bash
cd apps/api
cp .env.example .env
npm install
npx prisma generate
npx prisma db push
npm run db:seed
npm run dev          # http://localhost:4000/docs
npm test             # اختبارات منطق الخطط
```

## الإنتاج (PostgreSQL/Supabase)
استخدم المخطط الرسمي في جذر المشروع `prisma/schema.prisma` ‏(provider=postgresql + enums حقيقية):
انسخه إلى `apps/api/prisma/schema.prisma`، ضع `DATABASE_URL` و`DIRECT_URL`، ثم `npx prisma migrate deploy`.
الكود متوافق مع الاثنين ‏(قيم الحالات نصوص ثابتة).

## ملاحظات
- Google OAuth يعمل فقط عند ضبط `GOOGLE_CLIENT_ID/SECRET`.
- Stripe: الكود كامل ‏(Checkout + Webhook يحدّث الخطة) لكنه خامل بدون مفاتيح — checkout يرجع 503 برسالة واضحة.
- حد FREE: تأخير 60 دقيقة + 3 إشارات يوميًا + تحليل أساسي؛ PRO/VIP فوري وكامل.
