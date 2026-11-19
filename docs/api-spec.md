# API Spec (مسودة Phase 1 — تُوثَّق فعليًا بـ Swagger في Phase 3)

Base: `http://localhost:4000` — كل الردود JSON، الأخطاء `{ statusCode, message }`.

## Auth
| Method | Path | الوصف |
|---|---|---|
| POST | `/auth/register` | تسجيل Email + Password |
| POST | `/auth/login` | دخول → JWT |
| GET | `/auth/google` | بدء Google OAuth |
| GET | `/auth/google/callback` | إتمام OAuth |
| GET | `/auth/me` | المستخدم الحالي |

## Signals
| Method | Path | الوصف |
|---|---|---|
| GET | `/signals?status=READY&strategy=A&symbol=BTCUSDT` | التوصيات الحية (مفلترة حسب الخطة) |
| GET | `/signals/:id` | تفاصيل إشارة + تحليلها |
| GET | `/coins/:symbol/analysis` | آخر تحليل ICT لعملة (Bias, POI, BSL/SSL, BTC context) |
| GET | `/coins/:symbol/candles?tf=1h&limit=200` | شموع للشارت |
| WS | `/ws/signals` | بث إشارات READY الجديدة وتحديثات الحالة |

## Users
| Method | Path | الوصف |
|---|---|---|
| GET/PUT | `/users/me/preferences` | رصيد، مخاطرة، رافعة، حد Score |
| GET/POST/DELETE | `/users/me/watchlist` | العملات المفضلة |
| GET/PUT | `/users/me/notification-preferences` | قنوات التنبيه + Telegram |

## Subscriptions (Stripe — كود جاهز، تفعيل لاحق)
| Method | Path | الوصف |
|---|---|---|
| GET | `/subscriptions/plans` | Free/Pro/VIP |
| POST | `/subscriptions/checkout` | جلسة Stripe Checkout |
| POST | `/subscriptions/webhook` | Stripe Webhooks |
| GET | `/subscriptions/me` | اشتراكي الحالي |

## News & Journal & Stats
| Method | Path | الوصف |
|---|---|---|
| GET | `/news?symbol=BTC` | أخبار |
| GET | `/calendar` | أحداث اقتصادية قادمة |
| CRUD | `/journal` | سجل الصفقات اليدوية |
| GET | `/stats/strategies` | أداء المسارات A–D |

## Internal (AI Engine → API، محمي بـ token)
| Method | Path | الوصف |
|---|---|---|
| POST | `/internal/analyses` | حفظ تحليل (بديل عن كتابة DB مباشرة) |
| POST | `/internal/signals` | حفظ/تحديث إشارة |
| POST | `/internal/outcomes` | تحديث نتيجة |
