# مصادر البيانات: تفاصيل Alpha Vantage

يُقرأ هذا الملف فقط عند طلب سعر تحقق من Alpha Vantage أو عند الشك في سعر Crypto.com.

0. **تحقق اختياري من السعر: Alpha Vantage (مربوط عند المستخدم)، يُستخدم عند الطلب أو عند الشك في سعر Crypto.com فقط:**
   - الأداة `mcp__Alpha_Vantage_MCP_Server__CURRENCY_EXCHANGE_RATE` بـ `from_currency` = الرمز (مثل `XRP`) و`to_currency` = `USD` و`datatype` = `json`. ترجع السعر اللحظي مع Bid وAsk ووقت آخر تحديث بتوقيت UTC. تُحمَّل بـ tool_search باسم Alpha Vantage إن لم تكن ظاهرة.
   - للأسهم وصناديق الـ ETF المرتبطة بالكريبتو (مثل IBIT أو COIN) استخدم `GLOBAL_QUOTE` بالرمز.
   - عند ذكر السعر اذكر أنه من Alpha Vantage مع وقته UTC، وقارنه بآخر إغلاق شمعة من Crypto.com لتكشف أي فرق كبير. لا تجلبه في كل تحليل.
   - **حدود Alpha Vantage على الخطة الحالية:** شموع الكريبتو داخل اليوم (`CRYPTO_INTRADAY`) مدفوعة وترجع خطأ rate_limit، فلا تعتمد عليها للشموع. ولا تستخدم `DIGITAL_CURRENCY_DAILY` للشارت لأن ردّه يتجاوز 200 ألف توكن. الشموع تبقى من Crypto.com (البند 1). وإن تغيّرت الخطة فجرّب `CRYPTO_INTRADAY` مرة واحدة فقط.
