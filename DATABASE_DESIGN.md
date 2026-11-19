# DATABASE DESIGN — Crypto AI Signals Platform

> PostgreSQL (Supabase) + Redis (Upstash). المصدر: `prisma/schema.prisma`.
> NestJS يملك الـ Migrations (Prisma Migrate). Python AI Engine يكتب في نفس الجداول عبر SQLAlchemy أو Internal API محمي.

---

## 1. خريطة الكيانات (ERD نصي)

```
User ──1:1── Subscription ──1:N── Payment
User ──1:1── UserPreference
User ──1:N── WatchlistItem
User ──1:N── NotificationPreference / Notification / AlertSubscription
User ──1:N── TradeJournalEntry / ApiKey

Symbol ──1:N── Candle
Symbol ──1:N── Analysis ──1:N── Signal ──1:1── SignalOutcome
                              Signal ──1:N── Notification
                              Signal ──1:N── AlertSubscription

NewsItem / EconomicEvent   (مستقلة، تُربط منطقيًا بالرمز والوقت)
StrategyStats              (تجميعات أداء دورية)
EngineRun                  (سجل كل دورة فحص)
```

---

## 2. الجداول ووظيفتها

### المستخدمون والاشتراكات
| الجدول | الوظيفة |
|---|---|
| `users` | حسابات (Email + Google)، الخطة الحالية، اللغة/المنطقة الزمنية |
| `subscriptions` | حالة Stripe: الخطة، الفترة، التجديد/الإلغاء |
| `payments` | فواتير Stripe |
| `user_preferences` | رصيد افتراضي، مخاطرة 1%، رافعة، حد Score للتنبيه، المسارات المفعّلة |
| `watchlist_items` | عملات المستخدم المفضلة |

### بيانات السوق
| الجدول | الوظيفة |
|---|---|
| `symbols` | الأزواج المعتمدة الثمانية (+ قابلية إضافة) |
| `candles` | OHLCV مغلقة لكل فريم — فهرس فريد `(symbol, timeframe, openTime)` يمنع التكرار (نفس قاعدة الـ Skills: شمعتان بنفس الوقت = بيانات فاسدة) |

### محرك الذكاء
| الجدول | الوظيفة |
|---|---|
| `analyses` | كل فحص: Bias، Regime، ADX/ATR، لقطة هيكل ومناطق JSON، سياق BTC، إثراء Nansen/السيولة — تدقيق كامل |
| `signals` | الإشارة: مسار A–D، اتجاه، حالة، Score وتفصيله، منطقة دخول، SL/TP1/TP2، RR، إبطال، سبب عربي/إنجليزي، توقيتات الحالة |
| `signal_outcomes` | النتيجة: R المحقق، مدة، MAE/MFE — وقود التعلم |
| `strategy_stats` | Profit Factor / Expectancy / Net R / Drawdown لكل مسار×زوج×Regime + علم "معتمد" |
| `engine_runs` | كل دورة فحص كل 5 دقائق: بدء/انتهاء/أخطاء |

### الأخبار والتنبيهات
| الجدول | الوظيفة |
|---|---|
| `news_items` | أخبار الكريبتو مع رموز متأثرة وتأثير ومشاعر |
| `economic_events` | تقويم اقتصادي لنافذة إيقاف الأخبار (±30 دقيقة) |
| `notification_preferences` | قنوات المستخدم (Telegram/Email/Push/In-App) + Telegram chat id |
| `notifications` | كل إشعار مرسل مع حالته وخطئه |
| `alert_subscriptions` | تنبيهات سعرية يدوية بأسلوب TradingView (السعر \| الاتجاه \| النص) |

### الجورنال
| الجدول | الوظيفة |
|---|---|
| `trade_journal_entries` | صفقات المستخدم الفعلية — سعر خروج وحجم ورسوم **فعلية فقط، لا افتراضات** (قاعدة `journal.md`) |

---

## 3. قرارات تصميم مهمة

1. **JSON للقطات التحليل** (`structureJson`, `poiJson`, `scoreBreakdown`): الهيكل والمناطق متغيرة الشكل بين المسارات، وتحتاج إعادة عرض على الشارت وتدقيقًا لاحقًا. الحقول التي نفلتر/نفرز بها (score, status, strategy, side) أعمدة حقيقية مفهرسة.
2. **حالة الإشارة منفصلة عن نتيجتها:** `signals.status` دورة حياة، `signal_outcomes.result` حصيلة — يسمح بمتابعة الصفقات المفتوحة وتحديث MAE/MFE دون لمس الإشارة الأصلية.
3. **لا حذف للإشارات المرفوضة:** Score < 5 يُحفظ للتعلم والتحليل (مع `grade=REJECTED`) لكنه لا يُعرض كصفقة ولا يُنبَّه عنه.
4. **الأسعار Float:** كافية لمنصة إشارات (ليست محرك تنفيذ). عند إضافة تنفيذ حقيقي لاحقًا تُراجع إلى Decimal.
5. **Redis (Upstash) خارج Prisma:** Cache للشموع والأسعار الحية، BullMQ Queues (تنبيهات/أخبار)، Rate-limit، وPub/Sub للبث الحي عبر WebSocket.
6. **صلاحيات الخطط:** Free يرى إشارات متأخرة/محدودة، Pro/VIP فورية وكاملة — تُفرض في طبقة API (Guards) لا في قاعدة البيانات.

## 4. فهارس أساسية
- `candles(symbol_id, timeframe, open_time)` فريد — منع التكرار + استعلامات فريم سريعة.
- `signals(symbol_id, status)` و `signals(status, score)` — صفحة التوصيات الحية.
- `analyses(symbol_id, created_at)` — آخر تحليل لكل عملة.
- `notifications(user_id, created_at)` و `notifications(status)` — صندوق الوارد وطابور الإرسال.
- `news_items(published_at)`، `economic_events(scheduled_at)` — فلتر الأخبار.

## 5. التهيئة
```bash
cd apps/api
npx prisma migrate dev --name init   # ينشئ الجداول من schema.prisma
npx prisma db seed                    # يزرع الرموز الثمانية + مستخدم تجريبي
```
ملف الـ Seed يُبنى في Phase 3 مع الـ API. في Phase 1 الـ Schema هو العقد الملزم بين الخدمات.
