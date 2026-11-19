# Crypto AI Signals Platform

منصة SaaS مستقلة لتحليل العملات الرقمية بمنهجية ICT/SMC — محرك ذكاء Rules-Based يعمل على سيرفراتنا 24/7، بدون أي اعتماد على Claude أو أدوات خارجية بعد الإطلاق.

> ⚠️ أداة تحليل تعليمية. ليست نصيحة مالية، ولا تنفّذ صفقات نيابة عنك.

## الحالة: المنصة كاملة — المراحل 1–6 مكتملة ✅
- [x] **Phase 1:** تحليل Skills → `STRATEGY_SPEC.md` + تصميم قاعدة البيانات + هيكل Monorepo
- [x] **Phase 2:** AI Engine المستقل (Python/FastAPI) + Binance/CoinGecko
- [x] **Phase 3:** Backend API (NestJS) + Auth + نظام التوصيات + Swagger
- [x] **Phase 4:** Frontend كامل (Next.js: Landing + Dashboard)
- [x] **Phase 5:** News Agent + Notifications (Telegram + Email)
- [x] **Phase 6:** Docker + نشر + دليل تطوير

## الهيكل
```
crypto-ai-platform/
├── apps/
│   ├── web/              Next.js 14 — الواجهة (Vercel)
│   └── api/              NestJS — الـ API (Railway/Render)
├── services/
│   ├── ai-engine/        Python FastAPI — محرك ICT (فحص كل 5 دقائق)
│   └── worker/           Node BullMQ — تنبيهات وأخبار ومتابعة نتائج
├── packages/
│   ├── shared-types/     أنواع مشتركة
│   ├── ui/               مكونات واجهة مشتركة
│   └── config/           إعدادات مشتركة
├── prisma/schema.prisma  عقد قاعدة البيانات (PostgreSQL)
├── config/strategies.json  تحكم كامل بالاستراتيجيات بدون تعديل كود
├── STRATEGY_SPEC.md      كل قواعد ICT كدوال برمجية
├── ARCHITECTURE.md       المعمارية وتدفق البيانات
├── DATABASE_DESIGN.md    شرح الجداول والفهارس
├── docs/                 API spec + Deploy + Contributing
└── phase1-input/         ملفات Skills الأصلية (مرجع)
```

## التشغيل على جهازك (حاليًا: قاعدة بيانات فقط)
المرحلة 1 تصميم وهيكل — لا كود تشغيلي بعد. للتحقق من البيئة:
```bash
# 1) انسخ الإعدادات
cp .env.example .env

# 2) شغّل PostgreSQL + Redis محليًا
docker compose up -d postgres redis

# 3) تحقق من ملف الاستراتيجيات
cat config/strategies.json
```
الكود القابل للتشغيل يبدأ من Phase 2 (AI Engine) — انظر `PHASE1_SUMMARY.md` للتفاصيل.

## المستندات
- [STRATEGY_SPEC.md](./STRATEGY_SPEC.md) — تحويل Skills إلى دوال ومسارات A–D وScore
- [ARCHITECTURE.md](./ARCHITECTURE.md) — الخدمات والنشر
- [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) — الجداول والعلاقات
- [docs/api-spec.md](./docs/api-spec.md) — مسودة الـ API
