# Worker Service (BullMQ) — Phase 5 ✅

خدمة خلفية: أخبار كريبتو + تقويم اقتصادي + تنبيهات إشارات READY عبر Telegram وEmail.

## المهام (Jobs)
| المهمة | الفترة | المصدر | الجدول |
|---|---|---|---|
| `news` | كل 15 دقيقة | RSS: CoinDesk + CoinTelegraph + Decrypt (بدون مفاتيح) | `news_items` (تصنيف تأثير/رموز/مشاعر حتمي) |
| `calendar` | كل 6 ساعات | ForexFactory JSON الأسبوعي (USD، High/Medium) | `economic_events` |
| `notify` | كل دقيقة | إشارات READY آخر 24 ساعة | `notifications` |

## منطق التنبيه
- يحترم بوابة الخطط: FREE بعد 60 دقيقة، PRO/VIP فوري.
- يحترم تفضيلات المستخدم: حد Score الأدنى، المسارات المفعّلة، والعملات المفضلة (إن وُجدت).
- قنوات: Email (SMTP) وTelegram (Bot API + Chat ID من الإعدادات).
- **بدون مفاتيح = dry-run صادق**: يُسجَّل الإشعار FAILED مع سبب واضح ولا يُدّعى الإرسال. التكرار ممنوع (SENT وdry-run يمنعان إعادة الإرسال؛ الفشل الحقيقي يُعاد).
- نص التنبيه عربي كامل: دخول/SL/TP1/TP2/RR + قواعد TP1 جزئي 50% ونقل الوقف للتعادل.

## الربط مع المحرك
المحرك يقرأ `economic_events` في كل فحص ويطبّق فلتر الـ blackout ‏(±30 دقيقة حول أحداث HIGH) قبل اعتماد أي إشارة READY.

## التشغيل
```bash
cd services/worker
cp .env.example .env   # DATABASE_URL = نفس قاعدة الـ API
npm install
npx prisma generate
npm run build && npm start        # BullMQ + Redis (أو جدولة داخلية عند غياب Redis)
# أو مهمة واحدة بدون Redis:
npm run job:news | job:calendar | job:notify
npm test                          # 10 اختبارات وحدات
```

## تفعيل الإرسال الحقيقي
- Telegram: أنشئ بوتًا عبر @BotFather وضع `TELEGRAM_BOT_TOKEN`، والمستخدم يضع Chat ID في الإعدادات.
- Email: ضع `SMTP_HOST/PORT/USER/PASS/FROM`.
