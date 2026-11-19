# AI Engine Service (Python + FastAPI) — Phase 2 ✅

خدمة مستقلة تعمل 24/7: تفحص السوق كل 5 دقائق، تحسب مؤشرات ICT/SMC، تشغّل المسارات A–D، تحفظ التحليلات والإشارات، وتتابع النتائج للتعلم.

## الهيكل
```
app/
  main.py        FastAPI: /health /config /scan /analyze/{symbol} /signals /backtest /stats
  core/          config (strategies.json), scoring (Score/10), filters, risk (حجم الصفقة)
  indicators/    structure (Swing/BOS/CHoCH/IDM/BSL/SSL), poi (FVG/OB/BB/RJB/FZ/BCD),
                 technicals (EMA/SMA/ATR/ADX/Regime — TA-Lib اختياري مع بديل Python نقي)
  strategies/    base + A Continuation, B Sweep Reversal, C Breakout Retest, D Mean Reversion
  services/      market_data (Binance + CoinGecko), scanner, repository (حفظ + متابعة نتائج),
                 backtest (Walk-Forward)، learning (إحصاءات + اقتراح أوزان sklearn)
  models/        SQLAlchemy (مرآة Prisma — SQLite افتراضيًا، Postgres عبر DATABASE_URL)
tests/           9 Unit Tests
```

## التشغيل
```bash
cd services/ai-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# افتح http://localhost:8000/docs
```

جرّب:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/analyze/BTCUSDT
curl -X POST http://localhost:8000/scan
curl -X POST http://localhost:8000/backtest -H 'Content-Type: application/json' \
  -d '{"symbol":"BTCUSDT","timeframe":"1h","mode":"all","limit":1000}'
pytest tests/ -q
```

## متغيرات البيئة
- `DATABASE_URL` — Postgres في الإنتاج؛ بدونها SQLite محلي `ai_engine.db`
- `BINANCE_BASE_URL` — افتراضي `https://data-api.binance.vision` (بيانات عامة، قيود جغرافية أقل)
- `AI_ENGINE_INTERNAL_TOKEN` — حماية endpoints الداخلية
- `DISABLE_SCHEDULER=1` — إيقاف الفحص التلقائي (للاختبار)
- `STRATEGIES_CONFIG` — مسار بديل لملف الاستراتيجيات

ملاحظة: `api.binance.com` قد يرفض بعض المناطق جغرافيًا؛ نقطة `data-api.binance.vision` بنفس الشكل وتعمل على نطاق أوسع. على VPS في منطقة مدعومة يمكنك التبديل عبر المتغير.
