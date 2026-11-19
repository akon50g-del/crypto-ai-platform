# ملخص المرحلة 2 — AI Engine المستقل + Binance/CoinGecko

## ما تم بناؤه (كود حقيقي قابل للتشغيل في `services/ai-engine/`)

### المؤشرات والقلب (`app/indicators/` + `app/core/`)
- **structure.py:** Swing ‏(n=2، تأكيد بعد n شمعة)، Bias ‏(HH+HL/LH+LL)، BOS، CHoCH/MSS بالإغلاق، IDM + سحبه، BSL/SSL، Equal Highs/Lows ‏(0.15%)، Liquidity Sweep، OTE، Premium/Discount.
- **poi.py:** FVG بحالات unfilled/partial/filled، Order Block ‏(جسم/فتيل)، Breaker/Mitigation، Rejection، Flip Zone، BCD، Displacement ‏(1.5× + حجم).
- **technicals.py:** EMA/SMA/ATR/ADX/Regime — يستخدم TA-Lib إن وُجد، وإلا تنفيذ Python نقي مكافئ (نفس أرقام `backtest_ict.py`).
- **scoring.py:** Score الموحد من 10 كما في المواصفة تمامًا.
- **risk.py:** حجم صفقة مطابق لـ `position_size.py` + RR + أهداف من سيولة فعلية + SL بهامش ATR.
- **filters.py:** RR ≥ ‏1:2، توافق فريمات، سياق BTC، حظر أخبار ±30د، ATR شاذ، إشارة نشطة واحدة، حد ارتباط.

### الاستراتيجيات (`app/strategies/`)
- **A** Continuation، **B** Sweep Reversal ‏(Sweep+MSS شرطان صارمان)، **C** Breakout Retest ‏(EMA/ADX/Donchian)، **D** Mean Reversion في النطاق — كل مسار ملف مستقل يرث `BaseStrategy` ويُفعَّل من `config/strategies.json`.

### البيانات والخدمات (`app/services/`)
- **market_data.py:** Binance REST ‏(شموع مغلقة فقط — تُحذف الشمعة المتشكلة) + CoinGecko احتياطي للسعر + محمّل CSV يرفض الشموع المكررة + Cache.
- **scanner.py:** دورة فحص كاملة ‏(8 أزواج × مسارات مفعّلة) تحفظ Analysis دائمًا وSignals عند WATCH/READY، مع تخفيض READY→WATCH عند وجود إشارة نشطة أو تجاوز حد الارتباط.
- **repository.py:** حفظ SQLAlchemy ‏(SQLite افتراضيًا للتشغيل الفوري، Postgres عبر `DATABASE_URL`) + متابعة نتائج ‏(TP1 جزئي → Break-even → TP2/SL، وقاعدة SL أولًا).
- **backtest.py:** Walk-Forward منقول من `backtest_ict.py` ‏(رسوم/انزلاق بوحدات R، تقسيم In/Out-of-Sample، علم قبول ≥100 صفقة + PF ≥ ‏1.20).
- **learning.py:** إحصاءات لكل مسار/زوج/Regime + اقتراح أوزان Scikit-learn **للعرض فقط** ‏(مقفل حتى 100 صفقة مغلقة، ولا يُطبَّق تلقائيًا أبدًا).

### API والمجدول (`app/main.py`)
- FastAPI: ‏`/health` `/config` `/scan` `/analyze/{symbol}` `/signals` `/backtest` ‏(+ CSV) `/stats` — مع Swagger على `/docs`.
- مجدول APScheduler يفحص كل 5 دقائق ‏(من الإعدادات، قابل للإيقاف بـ `DISABLE_SCHEDULER=1`).
- `Dockerfile` جاهز ‏(TA-Lib اختياري معلّق).

## التحقق الفعلي (نتائج حقيقية من هذه الجلسة)
- **9/9 Unit Tests ناجحة** ‏(Swing, FVG, OB/Displacement, EMA/ATR/ADX, Score, Risk, CSV, Backtest, حواجز C/D).
- **فحص حي BTCUSDT ‏(2026-11-19 ‏17:40 UTC):** السعر ‏63,050 ‏(Binance)، Bias ‏4H هابط، Regime ‏1H صاعد، ADX ‏32.8، BSL فوق ‏[63300, 64080.8, ...]، SSL تحت ‏[62388.72, ...]، ‏6 FVG مفتوحة و4 OB — ولا مرشح إشارة في تلك اللحظة ‏(سلوك صحيح: لا صفقات مفروضة).
- **باكتيست BTC ‏1H على 999 شمعة حقيقية:** A ‏3 صفقات PF ‏0.819، B ‏0، C ‏8 صفقات PF ‏0.524، D ‏11 صفقة PF ‏2.436 وNet ‏+6.26R — **لا مسار "معتمد" بعد** لأن العينات أصغر بكثير من شرط 100 صفقة. هذا متوقع وصحي: الاعتماد يحتاج عينات أكبر ‏(هدف 3,000 شمعة/فريم) كما في البروتوكول.
- دورة فحص ‏(BTC+ETH) حُفظت في قاعدة البيانات بدون أخطاء، وواجهة API استجابت ‏(health/signals/stats/analyze).

## ملاحظات بيئة مهمة
- `api.binance.com` يرفض بعض المناطق جغرافيًا ‏(ظهر في بيئة الاختبار هذه). الافتراضي الآن `data-api.binance.vision` ‏(بيانات سوق عامة بنفس الشكل) وقابل للتبديل عبر `BINANCE_BASE_URL` على سيرفرك.
- TA-Lib غير مثبت في بيئة الاختبار — المحرك يعمل بالتنفيذ النقي المكافئ؛ تفعيله اختياري في Docker.

## كيف تشغّله على جهازك
```bash
cd crypto-ai-platform/services/ai-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# ثم: http://localhost:8000/docs
curl http://localhost:8000/analyze/BTCUSDT
curl -X POST http://localhost:8000/scan
pytest tests/ -q
```
بدون أي إعدادات إضافية يعمل بقاعدة SQLite محلية؛ للربط بـ Supabase ضع `DATABASE_URL` في البيئة.

## المرحلة التالية (Phase 3)
Backend API ‏(NestJS + Prisma): Auth ‏(Email + Google)، نظام التوصيات والبث الحي، اشتراكات Free/Pro/VIP ‏(Stripe مهيأ)، Swagger كامل.

**هل أكمل للمرحلة التالية؟**
