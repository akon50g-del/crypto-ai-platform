# المساهمة والتطوير — Crypto AI Signals Platform

## بنية المشروع
```
apps/web/            Next.js 14 (واجهة عربية RTL)
apps/api/            NestJS + Prisma (API + WebSocket)
services/ai-engine/  Python FastAPI (محرك ICT/SMC)
services/worker/     BullMQ (أخبار + تقويم + تنبيهات)
prisma/schema.prisma المخطط الرسمي PostgreSQL (19 نموذجًا)
config/strategies.json  مصدر الحقيقة الوحيد لضبط الاستراتيجيات
STRATEGY_SPEC.md     تحويل قواعد Skills إلى دوال حتمية (مرجع ملزم)
```

## قواعد لا تُكسر (من الـ Skills)
1. **شموع مغلقة فقط** — لا Look-Ahead في أي مؤشر أو باكتيست.
2. **Score موحد من 10** — تنفيذ ≥7، مراقبة 5–6، رفض <5. لا تغيير للأوزان بدون باكتيست.
3. **RR نهائي ≥ 1:2** وفلاتر §7 كلها إلزامية — أي فشل = لا إشارة.
4. **اعتماد مسار** يحتاج ≥100 صفقة مغلقة + Profit Factor ≥1.20 + Out-of-Sample ناجح. لا يُفعَّل مسار خاسر.
5. **لا تنفيذ آلي** في الإطلاق — إشارات وتنبيهات فقط، مع تنبيه دائم أنها ليست نصيحة مالية.
6. Nansen وLiquidations **طبقتا تأكيد فقط** — لا تدخلان الـ Score أبدًا.
7. لا Claude API ولا LLM في التشغيل اليومي — المحرك Rules + ML محلي فقط.

## إضافة استراتيجية جديدة
1. أنشئ `services/ai-engine/app/strategies/strategy_x_name.py` يرث `BaseStrategy` ويرجع `SignalCandidate`.
2. أضف مدخلًا في `config/strategies.json` ‏(`enabled: false` حتى الاعتماد).
3. اكتب اختبارات في `services/ai-engine/tests/` + باكتيست Walk-Forward.
4. لا تفعّلها قبل استيفاء قاعدة الاعتماد أعلاه.

## تشغيل الاختبارات
```bash
cd services/ai-engine && .venv/bin/python -m pytest tests/ -q     # 12 اختبارًا
cd apps/api && npm test                                           # منطق الخطط
cd services/worker && npm test                                    # تصنيف + مستلمون
cd apps/web && npm run build                                      # تحقق بناء
```

## قاعدة البيانات
- الرسمي: `prisma/schema.prisma` ‏(PostgreSQL). نسخ SQLite المحلية في `apps/api` و`services/worker` مولّدة عبر `make-sqlite-schema.py` — عدّل الرسمي ثم أعد التوليد.
- في Docker يُستبدل المخطط المحلي بالرسمي تلقائيًا ‏(سياق بناء = جذر المشروع).

## أسلوب الكود
- أسماء الحقول في DB بـ camelCase مطابقة لـ Prisma في كل الخدمات ‏(Python/Node).
- كل خدمة مستقلة: لا تستورد خدمة من أخرى — التواصل عبر DB أو HTTP داخلي فقط.
- الأسرار في `.env` فقط، لا تُحفظ في الكود أو الذاكرة.
