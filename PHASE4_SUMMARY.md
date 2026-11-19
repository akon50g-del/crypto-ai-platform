# ملخص المرحلة 4 — Frontend (Next.js 14)

## ما تم بناؤه (في `apps/web/`)

### الصفحات (13 مسارًا، عربية RTL، Mobile First)
- **Landing** (`/`): بطل تسويقي، مزايا، المسارات A–D، الأسعار، تنبيه مخاطر.
- **Pricing** (`/pricing`): خطط حية من API + زر ترقية Stripe ‏(رسالة واضحة إن الدفع غير مفعّل).
- **Auth**: `/login` و`/register` ‏(Email + Google عبر API) و`/auth/callback` لتوكن Google. Zustand + JWT في المتصفح، وحماية صفحات التطبيق.
- **Dashboard**: مفضلة، أحدث إشارات READY، أداء المسارات ‏(PF/Net R)، تنبيه ترقية للـ FREE.
- **Signals**: فلاتر ‏(حالة/مسار/عملة) + **بث WebSocket فوري** مع مؤشر اتصال — تتحدث القائمة عند كل إشارة جديدة.
- **Coin Details** (`/coin/[symbol]`): شارت شموع Lightweight Charts مع خطوط الدخول/SL/TP1/TP2 من أحدث إشارة ‏(نفس منطق `chart_draw.py`)، لوحة تحليل ICT ‏(Bias/Regime/BSL/SSL/FVG/OB/سياق BTC — التفاصيل مقفلة للـ FREE)، حاسبة حجم صفقة ‏(مرآة `position_size.py`)، وإشارات العملة.
- **News**: أخبار + تقويم اقتصادي ‏(تُملأ في Phase 5).
- **Journal**: إضافة وعرض صفقات بقيم فعلية فقط.
- **Settings**: رصيد/مخاطرة/رافعة/حد Score، عملات مفضلة، قنوات تنبيه Email/Telegram + Chat ID.
- **Billing**: الخطة الحالية والمدفوعات.

### مكونات وتصميم
- Nav متجاوب: شريط علوي + شريط تنقل سفلي للموبايل داخل التطبيق.
- SignalCard موحدة ‏(Score/Grade/RR/نتيجة)، ثيم داكن ‏(أخضر/أحمر للصعود/الهبوط، ذهبي للتمييز) بمصطلحات ICT الإنجليزية داخل نص عربي كما في Skills.

## التحقق الفعلي
- `npm run build` نجح: ‏13/13 مسارًا ‏(12 ثابتة + صفحة عملة ديناميكية)، أكبر حزمة صفحة عملة ‏151KB ‏(الشارت).
- تشغيل فعلي: Landing وLogin وPricing تُعرض بمحتواها العربي، وصفحة Signals تستجيب ‏200 ‏(الحماية تتم من جهة العميل بالتحويل لـ Login).
- التكامل مع API اختُبر في Phase 3 ‏(نفس العقود: ‏/auth, /signals, /coins, /users, /subscriptions, /stats, /journal, /news).

## كيف تشغّله على جهازك
```bash
# 1) API على 4000 (apps/api) + المحرك على 8000 (services/ai-engine)
cd crypto-ai-platform/apps/web
cp .env.example .env.local
npm install
npm run dev
# http://localhost:3000 — دخول تجريبي: demo@example.com / demo-password-123
```

## المرحلة التالية (Phase 5)
News Agent + Notifications: Worker بـ BullMQ يجلب الأخبار والتقويم، يرسل تنبيهات Telegram وEmail عند READY ‏(حسب خطة المستخدم وقنواته وحد الـ Score)، ويتابع نتائج الإشارات.

**هل أكمل للمرحلة التالية؟**
