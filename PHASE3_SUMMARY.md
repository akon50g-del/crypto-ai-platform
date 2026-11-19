# ملخص المرحلة 3 — Backend API (NestJS + Prisma)

## ما تم بناؤه (في `apps/api/`)

### Auth
- تسجيل/دخول Email + Password ‏(bcrypt ‏12 rounds + JWT ‏7 أيام)، `/auth/me`.
- Google OAuth ‏(Passport) — يُسجَّل تلقائيًا فقط عند ضبط `GOOGLE_CLIENT_ID/SECRET`، ويربط الحساب بنفس الإيميل إن وُجد.
- عند التسجيل تُنشأ تلقائيًا: Subscription ‏(FREE) + Preferences افتراضية.

### التوصيات والعملات
- `GET /signals` بفلاتر ‏(status/strategy/symbol) مع **بوابة خطط**: FREE = تأخير 60 دقيقة + 3 إشارات/يوم + تحليل أساسي، PRO/VIP = فوري وكامل.
- `GET /signals/:id` مع التحليل الكامل للمشتركين، `GET /coins/:symbol/analysis`، `GET /coins/:symbol/candles` ‏(Binance، شموع مغلقة فقط).
- WebSocket على `/ws/signals`: حدث `signal.ready` عند إنشاء إشارة READY.

### المستخدم والاشتراكات
- تفضيلات ‏(رصيد/مخاطرة/رافعة/حد Score/مسارات)، Watchlist، تفضيلات تنبيهات ‏(قناة + Telegram chat id)، صندوق إشعارات.
- Stripe كامل لكن خامل بدون مفاتيح: `plans` ‏(FREE ‏$0 / PRO ‏$19 / VIP ‏$49)، `checkout` يرجع 503 برسالة واضحة حتى تُضبط المفاتيح، `webhook` يحدّث الخطة عند الدفع/الإلغاء.

### الباقي
- أخبار + تقويم اقتصادي، Journal CRUD ‏(قيم فعلية فقط)، إحصاءات استراتيجيات ‏(PF/Expectancy/NetR + علم قبول)، Endpoints داخلية للمحرك ‏(`POST /internal/signals|outcomes` محمية بـ token)، Swagger كامل على `/docs`، Health check.

## قاعدة البيانات — قرار مهم
- المخطط الرسمي للإنتاج يبقى `prisma/schema.prisma` في الجذر ‏(PostgreSQL + Enums).
- للتطوير المحلي بدون Postgres: نسخة SQLite مولّدة آليًا في `apps/api/prisma/schema.prisma` عبر `make-sqlite-schema.py` ‏(Enum→String، قوائم→Json). الكود متوافق مع الاثنين. للإنتاج انسخ المخطط الرسمي واضبط `DATABASE_URL` ثم `prisma migrate deploy`.

## التحقق الفعلي (نتائج حقيقية)
- **3/3 Unit Tests** لمنطق بوابة الخطط ‏(تأخير FREE، سقف 3، PRO فوري).
- **Smoke test حي على الخادم:** تسجيل FREE ‏201، دخول Demo ‏(PRO) ‏201، إنشاء إشارة داخلية Score ‏8، مستخدم PRO يراها فورًا بينما FREE يرى 0 ‏(التأخير يعمل)، الخطط تُعرض مع `payments_enabled: false`، checkout بدون مفاتيح = 503، شموع BTC حية من Binance، Watchlist تعمل.
- ملاحظة بيئة: تنزيل Prisma Engines عبر Node في بيئة الاختبار هذه كان يتعطل ‏(ECONNRESET عبر البروكسي) فتم جلبه بـ curl يدويًا — على جهازك/سيرفرك يعمل `npm install` مباشرة بدون أي خطوة إضافية.

## كيف تشغّله على جهازك
```bash
cd crypto-ai-platform/apps/api
cp .env.example .env
npm install
npx prisma generate && npx prisma db push && npm run db:seed
npm run dev
# http://localhost:4000/docs — دخول تجريبي: demo@example.com / demo-password-123
```

## المرحلة التالية (Phase 4)
Frontend كامل ‏(Next.js ‏14): Landing + Auth + Dashboard + توصيات حية + تفاصيل عملة مع شارت ICT + أخبار + اشتراكات — Mobile First.

**هل أكمل للمرحلة التالية؟**
