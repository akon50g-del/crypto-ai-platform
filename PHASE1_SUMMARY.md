# ملخص المرحلة 1 — تحليل Skills + تصميم قاعدة البيانات + هيكل Monorepo

## ما تم بناؤه

### 1) تحليل الـ Skills وتحويلها إلى `STRATEGY_SPEC.md`
قرأت ملفيك بالكامل (`ict-crypto-analysis` بكل مراجعها وسكربتاتها + `ict-auto-trading-plan`) وحوّلت كل قاعدة إلى مواصفة برمجية حتمية:
- **Structure Engine:** Swing (n=2)، BOS، CHoCH/MSS بالإغلاق فقط، IDM، Bias، Displacement ‏(1.5× + حجم)، BSL/SSL و Equal Levels ‏(0.15%)، Liquidity Sweep، Market Regime ‏(ADX/EMA/ATR).
- **POI Detector:** FVG (غير المملوء فقط)، OB، BB، MB، RJB، IFC، OTE/FIBO ‏(0.62–0.79)، BCD، FZ — كل واحدة بقاعدة رقمية وقابلة للاختبار.
- **4 مسارات مستقلة:** A Continuation، B Sweep Reversal، C Breakout Retest ‏(EMA/ADX/Donchian)، D Mean Reversion في النطاق — كل مسار ملف مستقل يُفعَّل من JSON.
- **Score موحد من 10** (Bias ‏2 + POI ‏2 + Sweep ‏1 + MSS ‏2 + LTF ‏1 + سيولة ‏1 + RR ‏1) — تنفيذ عند ≥7، مراقبة 5–6، رفض <5.
- **9 فلاتر إلزامية** (RR ≥ ‏1:2، توافق فريمات، سياق BTC، أخبار ±30د، تقلب، عدم تكرار، إبطال، ارتباط ≤2، جلسات) + طبقتا تأكيد لا تدخلان في الـ Score ‏(Nansen، Liquidations).
- **Risk Engine** مطابق لـ `position_size.py`: مخاطرة 1%، حد يومي 2%، TP1 جزئي 50% عند 1–1.5R ثم Break-even، TP2 عند 2.5R/سيولة.
- **State Machine:** ‏NO_SETUP → WATCH → READY → TRIGGERED → CLOSED / INVALIDATED — التنبيه عند READY فقط.
- **Backtest Protocol** بشروط اعتماد صارمة (‏100 صفقة، Profit Factor ≥ ‏1.20، Out-of-Sample) ونظام تعلم من النتائج.
- **خريطة تحويل** من كل سكربت في Skills ‏(`ict_analyze.py`, `backtest_ict.py`, `position_size.py`, `chart_draw.py`) إلى موضعه في المنصة.

### 2) تصميم قاعدة البيانات — `prisma/schema.prisma` + `DATABASE_DESIGN.md`
- **المستخدمون:** users، subscriptions + payments ‏(Stripe جاهز كهيكل)، preferences، watchlist.
- **السوق:** symbols ‏(8 أزواج)، candles بفهرس فريد يمنع التكرار.
- **المحرك:** analyses ‏(لقطة تدقيق كاملة)، signals ‏(مسار/Score/مستويات/حالة)، signal_outcomes ‏(R و MAE/MFE للتعلم)، strategy_stats، engine_runs.
- **الأخبار والتنبيهات:** news_items، economic_events، notification_preferences، notifications، alert_subscriptions ‏(بأسلوب TradingView).
- **الجورنال:** trade_journal_entries بقاعدة "قيم فعلية فقط".
- Redis ‏(Upstash) للـ Cache و BullMQ و WebSocket Pub/Sub.

### 3) هيكل Monorepo كامل
```
apps/web (Next.js) · apps/api (NestJS) · services/ai-engine (Python) · services/worker (BullMQ)
packages/shared-types · ui · config
config/strategies.json — تحكم كامل بدون تعديل كود
docker-compose.yml (Postgres+Redis جاهزان، باقي الخدمات مُعلّقة حتى Phase 6)
.env.example · turbo/pnpm workspace · docs/api-spec.md · deploy.md · CONTRIBUTING.md
```

## كيف تشغّله على جهازك الآن
المرحلة 1 تصميم وهيكل (لا كود تشغيلي بعد — هذا مقصود حسب خطتك):
```bash
cd crypto-ai-platform
cp .env.example .env
docker compose up -d postgres redis   # قاعدة بيانات محلية للتجربة
cat STRATEGY_SPEC.md                   # راجع المواصفة
cat config/strategies.json             # راجع إعدادات المسارات والـ Score
```
كل الملفات موجودة في `~/workspace/crypto-ai-platform/` — يمكنك مراجعة `STRATEGY_SPEC.md` و`prisma/schema.prisma` والتأكد أن أي تعريف غامض في ICT محسوم رقميًا قبل أن نبرمجه.

## قرارات تحتاج تأكيدك قبل Phase 2 (إن أردت تعديلها)
1. مصدر الشموع الإنتاجي: **Binance REST** أساسي (بديل عن Crypto.com MCP) — أوافق؟
2. `swing_n=2` افتراضيًا (3 للفريمات الصغيرة) كما في سكربتاتك.
3. Nansen و Coinversa: طبقات تأكيد اختيارية معطّلة افتراضيًا حتى تتوفر مفاتيح API.
4. الإطلاق بمرحلة "تنبيهات فقط" — لا تنفيذ آلي.

## المرحلة التالية (Phase 2)
بناء AI Engine: مؤشرات ICT كدوال Python + اختبارات، ربط Binance، المسارات A–D، حفظ التحليلات/الإشارات، Backtester منقول من `backtest_ict.py`.

**هل أكمل للمرحلة التالية؟**
