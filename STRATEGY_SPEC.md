# STRATEGY SPEC — Crypto AI Signals Platform
## تحويل Skills إلى محرك Rules-Based + ML مستقل

> المصدر: `ict-crypto-analysis/SKILL.md` + `ict-auto-trading-plan/SKILL.md` + `references/*` + `scripts/*.py`
> الهدف: كل قاعدة بشرية في الـ Skills تصبح Function برمجية حتمية داخل `services/ai-engine`، بدون Claude API في التشغيل اليومي.
> القاعدة الحاكمة من الـ Skills: **شموع مغلقة فقط، لا Look-Ahead، لا صفقة بدون فلاتر كاملة، Score موحد من 10.**

---

## 1. فلسفة المحرك

```
Binance / Crypto.com / CoinGecko (OHLCV مغلقة)
        │
        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Market Regime    │ ──▶ │ Structure Engine │ ──▶ │ POI Detector     │
│ ADX / EMA / ATR  │     │ Swing/BOS/CHoCH  │     │ FVG/OB/BB/MB...  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                                                  │
        ▼                                                  ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ BTC Context      │ ──▶ │ Strategy A/B/C/D │ ──▶ │ Score + Filters  │
│ + News Filter    │     │ State Machine    │     │ RR ≥ 2 / Risk    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                        │
                                                        ▼
                                              Signal (READY only)
                                              → DB → API → UI → Notify
```

- المحرك يعمل كل **5 دقائق** (قابل للضبط في `config/strategies.json`) على 8 أزواج سائلة.
- كل تحليل يُحفظ في `signals` + `analyses` مع السبب والـ Score وتفاصيل كل مكوّن (قابل للتدقيق).
- التعلم: كل إشارة تُتتبع حتى TP/SL/Invalidated، والنتيجة تغذّي `signal_outcomes` لتعديل أوزان الـ Score لاحقًا (Scikit-learn في Phase 2+).

---

## 2. الأزواج والفريمات المعتمدة

| العنصر | القيمة | المصدر |
|---|---|---|
| الأزواج | BTC, ETH, SOL, XRP, BNB, DOGE, LINK, AVAX (USDT) | SKILL.md — قائمة السيولة المعتمدة |
| HTF Bias | 4H (+1D عند الحاجة لسياق أكبر) | Top-Down |
| منطقة الدخول | 1H (FVG + OB + OTE) | Top-Down |
| التأكيد | 15m (MSS/CHoCH + Displacement) | Top-Down |
| التنفيذ (اختياري) | 1m / 5m عند طلب المستخدم فقط | strategy_rules.md |
| الجلسات | London + New York (تركيز الفحص) | SKILL.md |
| حد الارتباط | صفقتان مترابطتان كحد أقصى مع BTC في الاتجاه نفسه | SKILL.md |

---

## 3. تعريفات هيكلية حتمية (Structure Engine)

كل تعريف = دالة Python نقية في `app/indicators/structure.py`، تُختبر بـ Unit Tests.

### 3.1 Swing High / Low
```
is_swing_high(candles, i, n=2): high[i] > high[i-k] AND high[i] > high[i+k]  ∀k∈[1..n]
is_swing_low(candles, i, n=2):  low[i]  < low[i-k]  AND low[i]  < low[i+k]   ∀k∈[1..n]
```
- `n=2` افتراضي (كما في `ict_analyze.py` و `backtest_ict.py`)، `n=3` للفريمات الصغيرة كثيرة الضجيج.
- الـ Swing لا يُعتمد إلا بعد إغلاق الشمعة `i+n` (منع Look-Ahead).

### 3.2 BOS — Break of Structure (استمرار)
- صاعد: `close > last_swing_high` بعد آخر قمة مؤكدة.
- هابط: `close < last_swing_low`.
- الفتيل وحده لا يكفي — **الإغلاق شرط**.

### 3.3 CHoCH / MSS — Change of Character / Market Structure Shift
- صاعد: `close > last_swing_high` في سياق هابط (كسر آخر قمة حقيقية).
- هابط: `close < last_swing_low` في سياق صاعد.
- يُستخدم على 15m داخل POI كتأكيد دخول، وعلى 4H/1H في الطريقة الثانية (انعكاس).

### 3.4 IDM — Inducement (الحافز)
- آخر قمة/قاع داخلي صغير قبل القمة/القاع الرئيسي.
- مسحوب = `wick > IDM` ثم `close` عائد داخل النطاق.
- **شرط صلاحية في الطريقة الثانية:** لا دخول قبل سحب الحافز.

### 3.5 Bias (4H)
| الحالة | الشرط |
|---|---|
| Bullish | HH + HL (آخر قمتين وقاعين تصاعديًا) |
| Bearish | LH + LL |
| Range | غير ذلك |

### 3.6 Displacement
```
body = |close - open|
avg_body = mean(|c-o| لآخر 20 شمعة قبل i)
displacement = body >= 1.5 × avg_body  AND  volume[i] >= mean(volume آخر 20) (إن توفر)
```
مطابق لـ `backtest_ict.py: displacement()` و `ict_analyze.py: order_blocks()`.

### 3.7 BSL / SSL — Buy-Side / Sell-Side Liquidity
- BSL: قمم Swing فوق السعر الحالي (أهداف صعود / مناطق سحب).
- SSL: قيعان Swing تحت السعر.
- Equal Highs/Lows: قمتان/قاعان ضمن تسامح `0.15%` (`tol=0.0015` في `ict_analyze.py`) = سيولة مجمّعة.

### 3.8 Liquidity Sweep
- Long sweep: `low < prior_swing_low AND close > prior_swing_low`
- Short sweep: `high > prior_swing_high AND close < prior_swing_high`
(مطابق لـ `confirmation()` في `backtest_ict.py`)

### 3.9 Market Regime (لاختيار المسار)
| النظام | الشرط | المسارات المسموحة |
|---|---|---|
| Trend Up/Down | ADX > 20 + EMA50/200 متوافقة + Bias واضح | A, C |
| Range | ADX < 18–20 + EMA50 مسطحة + نطاق 12–24 شمعة | D فقط |
| High Volatility | Range الشمعة الأخيرة > 1.5× Median آخر 20 | حذر: وقف بالفتائل، لا دخول متأخر |

---

## 4. مناطق الاهتمام POI (app/indicators/poi.py)

| المنطقة | القاعدة البرمجية الحتمية | ملاحظات |
|---|---|---|
| **FVG** | Bullish: `low[i] > high[i-2]` → المنطقة `[high[i-2], low[i]]`. Bearish عكسه. يُحسب **غير المملوء فقط**: لا شمعة لاحقة أغلقت/لمست الإلغاء الكامل. حالات: `unfilled / partial / filled` | FVG على 4H/1D أثقل وزنًا |
| **OB — Order Block** | آخر شمعة معاكسة قبل Displacement يكسر هيكلًا ويترك FVG. المنطقة: الجسم للدخول `[min(o,c), max(o,c)]`، الفتيل للوقف `[low, high]` | بحث للخلف حتى 5 شموع قبل الـ Displacement |
| **BB — Breaker Block** | OB كُسر بإغلاق، ثم عاد السعر لاختباره من الجهة الأخرى وكسر آخر قمة/قاع | |
| **MB — Mitigation Block** | مثل BB لكنه يرتد **قبل** كسر آخر قمة/قاع | |
| **RJB — Rejection Block** | شموع بذيول متساوية تقريبًا عند قمة/قاع حقيقي. المنطقة من الذيل المرفوض إلى الجسم | |
| **IFC — Institutional Funding Candle** | شمعة تسحب بفتيلها سيولة قمة/قاع/IDM دون إغلاق كامل خلفها. تُختبر لاحقًا | |
| **OTE / FIBO 0.62–0.79** | على آخر Leg: Short: `low + range×[0.62, 0.79]`، Long عكسه. نسخة FIBO 0.70–0.85 بشرط سحب IDM أولًا | تقاطع OTE+FVG+OB = أقوى منطقة |
| **BCD — Big Candle Displacement** | شمعة جسمها يبتلع آخر 4 شموع على الأقل بعد سحب سيولة. الدخول من فتيلها | |
| **FZ — Flip Zone** | منطقة كُسرت وأصبح عكسها مع CHoCH → دعم/مقاومة جديدة | دخول الطريقة الثانية |

**قاعدة التقاطع:** أقوى منطقة = FVG فريم أكبر + FVG 1H + OTE + OB. يُذكر صراحة في مخرجات التحليل ويُرفع الـ Score.

---

## 5. المسارات الأربعة (Strategies A–D)

كل مسار = ملف مستقل في `app/strategies/` يرث `BaseStrategy`، ويُفعَّل/يُعطَّل من `config/strategies.json` بدون تعديل كود.

### المسار A — ICT Continuation (مع الاتجاه) — `strategy_a_continuation.py`
1. Bias واضح على 4H (HH+HL أو LH+LL).
2. منطقة 1H فيها FVG أو OB متوافقة مع OTE و Premium/Discount.
3. سحب BSL/SSL قريب أو وصول لسيولة معروفة.
4. MSS/CHoCH + Displacement على 15m.
5. الدخول من إعادة اختبار FVG/OB **بعد إغلاق شمعة التأكيد**، لا أثناء الشمعة الحالية.
6. الهدف النهائي سيولة فعلية، RR نهائي ≥ 1:2.

### المسار B — Liquidity Sweep Reversal — `strategy_b_sweep_reversal.py`
1. وصول لــ BSL/SSL واضحة على 1H أو 4H.
2. Sweep فعلي ثم إغلاق عائد داخل النطاق.
3. MSS/CHoCH معاكس على 15m مع Displacement.
4. تتكون FVG بعد الـ Displacement؛ الدخول من إعادة اختبارها فقط.
5. SL خلف قمة/قاع الـ Sweep. إلغاء عند إغلاق خلف أصل الـ Sweep.
6. لا قبول بمجرد لمس المنطقة، ولا بدون Sweep+MSS، ولا RR < 1:2.

### المسار C — Trend Pullback / Breakout Retest — `strategy_c_breakout_retest.py`
1. 1H: السعر فوق EMA200 و EMA50 فوق EMA200 (شراء) والعكس للبيع؛ ADX > 20 وميل EMA50 متوافق.
2. 15m: كسر بإغلاق كامل مع حجم أعلى من المتوسط (Donchian 20).
3. الدخول بعد Retest لمستوى الكسر ورفض على 1m/5m.
4. SL خلف الـ Retest (±0.25×ATR)، TP1 عند 1.5R و TP2 عند السيولة التالية أو 2.5R.
5. ممنوع عند ADX < 18 أو قرب EMA200 مع تذبذب جانبي.
(مطابق لـ `breakout_setup()` في `backtest_ict.py` — يحتاج ≥230 شمعة.)

### المسار D — Mean Reversion في النطاق — `strategy_d_mean_reversion.py`
1. يعمل فقط مع ADX < 18–20 و EMA50 مسطحة ونطاق واضح 12–24 شمعة (عرض ≥ 2×ATR).
2. عند الحد السفلي: Sweep للقاع + إغلاق داخل النطاق + MSS صاعد على 1m/5m للشراء (والعكس علويًا).
3. TP1 منتصف النطاق (SMA20)، TP2 الطرف المقابل.
4. ممنوع عكس Displacement قوي أو خبر مرتفع التأثير.
(مطابق لـ `mean_reversion_setup()` في `backtest_ict.py`.)

### طريقتا الدخول في `ict-auto-trading-plan` (تُدمج داخل A/B)
- **الطريقة 1 (مع الاتجاه):** 4H BOS → سحب IDM على 1H/15m → سعر داخل POI → 15m CHoCH داخل المنطقة → فلاتر.
- **الطريقة 2 (بعد تغيّر الاتجاه):** POI كبير 4H → CHoCH على 4H/1H → سحب IDM الأخير → دخول من FZ أو OB خلف IDM. **لا دخول قبل سحب IDM.**

---

## 6. درجة القبول الموحدة — Score من 10

نظام واحد لكل المسارات (لا نظام درجات آخر). يُحسب في `app/core/scoring.py`:

| المكوّن | النقاط | الشرط |
|---|---|---|
| Bias واضح | 2 | 4H HH+HL أو LH+LL مؤكد |
| FVG/OB صالح | 2 | POI غير مملوء ومتوافق مع الاتجاه |
| Sweep | 1 | سحب BSL/SSL/IDM مؤكد بإغلاق عائد |
| MSS/CHoCH على 15m | 2 | كسر هيكل بإغلاق + Displacement |
| تأكيد LTF | 1 | شمعة رفض مغلقة داخل/خارج المنطقة باتجاه الـ Bias |
| سيولة مستهدفة | 1 | هدف = سيولة فعلية (Equal Lows/SSL/BSL) لا رقم نفسي |
| RR نهائي ≥ 1:2 | 1 | من سعر الدخول الفعلي |
| **المجموع** | **10** | |

| الدرجة | التصنيف | الإجراء |
|---|---|---|
| 8–10 | A+ | **منفَّذ** — إشارة READY + تنبيه |
| 7 | A | **منفَّذ** — إشارة READY + تنبيه |
| 5–6 | مراقبة | Watchlist + تنبيه سعري فقط، لا إشارة دخول |
| < 5 | مرفوض | يُسجَّل للتعلم فقط، لا يُعرض كصفقة |

> لمس المنطقة ≠ دخول. الشمعة الحالية غير المكتملة لا تُستخدم أبدًا.

---

## 7. الفلاتر الإلزامية (Filters — أي فشل = لا إشارة)

تُطبَّق كلها في `app/core/filters.py` قبل الانتقال إلى READY:

1. **RR:** الهدف النهائي (أو المتوسط المرجّح) ≥ 1:2 من الدخول الفعلي. TP1 قد يكون أقل لأنه إغلاق جزئي.
2. **توافق الفريمات:** لا شراء 15m مع هبوط واضح 4H (إلا الطريقة 2 / المسار B).
3. **سياق BTC:** منع صفقات بديلة معاكسة لهيكل BTC الحاد على 4H. كسر BTC لقاع نطاقه يلغي أوامر البيع المعلقة على العملات.
4. **الأخبار:** إيقاف التنبيهات قبل/بعد الأخبار المؤثرة بنافذة 30 دقيقة (تقويم اقتصادي — Phase 5).
5. **التقلب:** استبعاد ATR شاذ جدًا أو سوق راكد.
6. **عدم التكرار:** إشارة فعالة واحدة لكل عملة، وحد أدنى للفاصل بين التنبيهات.
7. **الإبطال:** كسر الوقف المحسوب قبل التفعيل يلغي الإعداد فورًا → `INVALIDATED`.
8. **الارتباط:** ≤ صفقتين مترابطتين مع BTC في الاتجاه نفسه؛ عند التزاحم يُختار الأعلى Score.
9. **الجلسة (اختياري):** تفضيل London/New York — قابل للضبط، لا يمنع الفحص خارجها لكن يوسم الجودة.

**طبقات تأكيد لا تدخل في الـ Score:**
- **Nansen (Smart Money):** تجميع أثناء تصحيح داخل OB/FVG يؤكد Long (والعكس Short). Inflow كبير للمنصات أثناء صعود = تحذير. لا يصنع Setup بمفرده.
- **Coinversa / Hyperliquid Liquidations:** تجمعات تصفية فوق/تحت السعر كطبقة تأكيد سيولة فقط (بيانات Hyperliquid لا Binance).

---

## 8. الوقف والأهداف والحجم (Risk Engine)

مطابق لـ `position_size.py` + قواعد الـ Skills:

```
risk_amount = balance × risk%          (افتراضي 1%، لا يرتفع لـ 2% إلا بعد 20 صفقة مغلقة مستقرة)
qty         = risk_amount / |entry − sl|
notional    = qty × entry
margin      = notional / leverage      (Isolated، رافعة منخفضة 2–3x، سقف حسب التقلب)
```

- **SL:** خلف أصل الحركة (قمة/قاع OB أو Leg أو Sweep) + Buffer 0.1–0.2×ATR. لا يُوضع داخل منطقة Equal Highs/Lows لأنها تُسحب.
- **TP1:** أقرب سيولة فعلية (Equal Lows/SSL أو قمة/قاع داخلي) — إغلاق ~50% عند 1R–1.5R ثم نقل SL إلى Break-even.
- **TP2:** آخر قمة/قاع رئيسي 4H أو السيولة التالية أو 2.5R عند توفرها.
- **الحد اليومي:** 2% خسارة. بعد خسارتين متتاليتين توقف حتى الجلسة التالية.
- الأرباح/الخسائر **قبل الرسوم والانزلاق** — تُذكر صراحة في الواجهة. الـ Short يحتاج Futures/Margin.
- الأوامر المعلقة: صلاحية 24–48 ساعة، SL مربوط دائمًا. إلغاء عند: إغلاق 1H خلف أصل الحركة، وصول السعر لـ TP1 قبل التنفيذ، كسر BTC لمستواه المفتاحي، خبر قوي خاص بالعملة.

---

## 9. حالات الإعداد — State Machine

```
NO_SETUP ──▶ WATCH ──▶ READY ──▶ TRIGGERED ──▶ CLOSED
   ▲           │          │           │
   └───────────┴──────────┴────▶ INVALIDATED
```

| الحالة | المعنى | تنبيه؟ |
|---|---|---|
| `NO_SETUP` | لا شيء | لا |
| `WATCH` | السعر داخل POI، بانتظار تأكيد 15m (Score 5–6 غالبًا) | تنبيه سعري اختياري |
| `READY` | اجتاز كل الشروط والفلاتر (Score ≥ 7) | **نعم — عند الانتقال فقط** |
| `TRIGGERED` | دخل السعر منطقة الدخول، صفقة افتراضية مفتوحة للمتابعة | إشعار دخول |
| `CLOSED` | وصل TP أو SL — تُسجَّل النتيجة (R, PnL, سبب الخروج) | إشعار نتيجة |
| `INVALIDATED` | كُسر الإبطال قبل التفعيل | إشعار إلغاء |

---

## 10. مصادر البيانات

| المصدر | الاستخدام | ملاحظات |
|---|---|---|
| **Binance REST** (أساسي في المنصة) | OHLCV 15m/1H/4H/1D + سعر حي | بديل إنتاجي عن Crypto.com MCP؛ نفس صيغة الشموع |
| Crypto.com | شموع بديلة / تحقق | حتى 50 شمعة/استدعاء في الـ Skill الأصلي — في المنصة نستخدم REST مباشرة |
| CoinGecko | أسعار إغلاق احتياطية + بيانات سوق | بدون فتائل → مناطق تقريبية ±1–2% مع تصريح |
| Alpha Vantage | تحقق سعري اختياري عند الشك | `CURRENCY_EXCHANGE_RATE` فقط؛ شموع intraday مدفوعة |
| Nansen | تدفقات Smart Money (تأكيد) | `token_info`, `token_recent_flows_summary` رخيصان؛ `top_holders` عند الطلب فقط (150 credit) |
| Coinversa Pulse | Liquidation Heatmap (Hyperliquid) | تأكيد سيولة فقط، لا مصدر سعر |

**قاعدة صارمة:** لا أرقام من الذاكرة. كل سعر مع مصدره ووقته UTC ونوع البيانات. اختلاف Crypto.com عن Binance ‏0.2–0.5% يُذكر في التحليل.

---

## 11. الاختبار الخلفي والاعتماد (Backtest Protocol)

مطابق لـ `references/backtest_protocol.md` + `scripts/backtest_ict.py`:

- شموع مغلقة فقط، Walk-Forward محافظ: لا استخدام للشمعة الحالية لاستخراج البنية.
- عينة مستهدفة 3,000 شمعة/فريم/زوج (تجميع CSV من Binance/TradingView).
- تقسيم 70% In-Sample / 30% Out-of-Sample + Walk-Forward. فصل Long/Short وكل مسار وكل Regime.
- تنفيذ واقعي: رسوم + انزلاق + Spread (بوحدات R: `--fee-r`, `--slip-r`). عند لمس SL وTP في نفس الشمعة → **SL أولًا**. محاكاة TP1 جزئي → Break-even → TP2.
- **شروط اعتماد أي مسار:** ≥100 صفقة مغلقة (أو أكبر عينة متاحة مع تصريح)، Profit Factor ≥ 1.20، Expectancy و Net R موجبان بعد التكاليف، Max Drawdown مقبول، نجاح Out-of-Sample، دون الاعتماد على صفقة/أسبوع واحد.
- فحص أولي (لا اعتماد): ≥200 شمعة/فريم + 20 صفقة لاستبعاد الأفكار الضعيفة فقط.
- لا تعديل معلمات بعد رؤية نتائج الاختبار إلا في دورة جديدة موثقة. فشل المسار = إيقافه والرجوع للأعلى Score.

---

## 12. نظام التعلم (Learning Loop — Phase 2+)

1. كل إشارة تُحفظ مع: المسار، Score وتفاصيله، Regime، الفريمات، مستويات الدخول/SL/TP، لقطة المؤشرات.
2. متابعة آلية حتى TP1/TP2/SL/Invalidated → `signal_outcomes` (R المحقق، مدة الصفقة، MAE/MFE).
3. تحليل دوري (كل 20 صفقة مغلقة): Win Rate و Profit Factor لكل مسار/زوج/Regime/جلسة.
4. نموذج Scikit-learn (Logistic Regression / Random Forest مبدئيًا) يتعلم أوزان مكوّنات الـ Score من النتائج — **لا يلغي قواعد ICT، بل يضبط الأوزان ضمن حدود آمنة** ويُعتمد فقط بعد اجتياز شروط الاعتماد نفسها.
5. سجل الصفقات اليدوية للمستخدم (Journal): دخول/خروج فعلي، حجم، رسوم، سبب الدخول، سكرين شوت — لا تُفترض قيم لم يذكرها المستخدم.

---

## 13. مراحل التشغيل (من ict-auto-trading-plan)

1. **تنبيهات فقط** — إشارات مقترحة دون تنفيذ، لقياس دقة القواعد. ← *إطلاق المنصة هنا*
2. **حساب تجريبي** — تنفيذ آلي افتراضي مع تسجيل كل صفقة.
3. **حساب حقيقي** — فقط بعد نجاح صارم في المرحلة السابقة، وبحجم صغير. الانتقال قرار المستخدم، لا تلقائي أبدًا.

زر طوارئ: إيقاف التنفيذ/التنبيهات وإغلاق المتابعة عند تجاوز خسارة يومية محددة.

---

## 14. خريطة التحويل: Skill → كود

| في الـ Skills | في المنصة |
|---|---|
| `ict_analyze.py: swings/fvgs/order_blocks/equal_levels` | `app/indicators/structure.py` + `poi.py` |
| `backtest_ict.py: ict_setup/breakout/mean_reversion` | `app/strategies/strategy_a..d.py` + `app/services/backtest.py` |
| `backtest_ict.py: displacement/confirmation/regime` | `app/indicators/displacement.py` + `regime.py` |
| `position_size.py` | `app/core/risk.py` (+ نسخة TypeScript في `packages/shared-types` للواجهة) |
| `candles.py` (تحميل CSV/JSON) | `app/services/market_data.py` (Binance REST + Cache Redis) |
| `chart_draw.py` | `apps/web` — Lightweight Charts مع Zones/Lines (Phase 4) |
| قالب الرد العربي (الخلاصة/لماذا/الصفقة/التنبيهات/الحجم) | مكونات UI في صفحة تفاصيل العملة + نص الإشعار |
| `references/journal.md` | جدول `trade_journal` + صفحة Journal |
| `references/liquidity.md` + `nansen.md` | `app/services/enrichment.py` (تأكيد اختياري، معطّل افتراضيًا بدون مفاتيح) |

---

## 15. إعدادات قابلة للضبط (`config/strategies.json`)

كل ما يلي يُضبط بدون تعديل كود: تفعيل كل مسار، `swing_n`، مضاعف Displacement (1.5)، أوزان الـ Score وحدود القبول (7/5)، RR الأدنى (2.0)، نسبة المخاطرة (1%)، الحد اليومي (2%)، فاصل الفحص (5 دقائق)، الأزواج، الفريمات، نافذة الأخبار (30 دقيقة)، حد الارتباط (2). انظر الملف نفسه للبنية الكاملة.

> ⚠️ التحليل تعليمي وليس نصيحة مالية. التداول عالي المخاطر، والمستخدم يتحمل قرار التنفيذ.
