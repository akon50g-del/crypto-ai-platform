# Frontend (Next.js 14 App Router) — Phase 4 ✅

واجهة SaaS عربية RTL متجاوبة Mobile-First: Landing، Auth، Dashboard، توصيات حية، تفاصيل عملة مع شارت ICT، أخبار، سجل صفقات، إعدادات، اشتراكات.

## الصفحات
```
src/app/
  page.tsx              Landing (مزايا، مسارات A–D، أسعار)
  pricing/              الخطط + ترقية Stripe (503 واضح حتى التفعيل)
  login/ register/      Email + Google (عبر API)
  auth/callback/        استلام توكن Google
  dashboard/            نظرة عامة: مفضلة + أحدث READY + أداء المسارات
  signals/              توصيات حية بفلاتر + بث WebSocket فوري
  coin/[symbol]/        شارت شموع ICT + تحليل + حاسبة حجم صفقة + إشارات العملة
  news/                 أخبار + تقويم اقتصادي
  journal/              سجل صفقات (قيم فعلية فقط)
  settings/             مخاطرة افتراضية + مفضلة + قنوات تنبيه (Email/Telegram)
  billing/              الخطة الحالية والمدفوعات
src/components/  Nav (شريط سفلي للموبايل)، SignalCard، IctChart، RiskCalculator، RequireAuth
src/stores/      Zustand: auth
src/lib/         api client + risk (مرآة position_size.py)
```

## التشغيل
```bash
# شغّل الـ API أولًا (apps/api على 4000) والمحرك (services/ai-engine على 8000)
cd apps/web
cp .env.example .env.local
npm install
npm run dev    # http://localhost:3000
npm run build  # تحقق إنتاجي
```
دخول تجريبي: demo@example.com / demo-password-123
