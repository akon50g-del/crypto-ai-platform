# تطبيق أندرويد (Capacitor) — Crypto AI Signals

التطبيق يغلّف واجهة الويب نفسها (`apps/web`) كتطبيق أندرويد أصلي عبر Capacitor،
ويتصل بالـ API المنشور على سيرفرك. نفس الكود، نفس الشاشات، أيقونة على الشاشة الرئيسية.

## طريقتان للحصول على التطبيق

### 1) PWA — بدون متجر وبدون بناء (الأسرع)
بعد نشر الموقع على سيرفرك (deploy.sh):
- افتح الموقع من Chrome على أندرويد → قائمة ⋮ → **"تثبيت التطبيق / Add to Home screen"**
- سيظهر كتطبيق بملء الشاشة بأيقونته الخاصة (manifest + Service Worker جاهزان)

### 2) APK أصلي عبر Capacitor
**أ) بدون Android Studio — عبر GitHub Actions (موصى به):**
1. ارفع المشروع إلى GitHub
2. في إعدادات الـ repo ‏(Settings → Variables) أضف `NEXT_PUBLIC_API_URL` و`NEXT_PUBLIC_WS_URL` بروابط سيرفرك
3. من تبويب Actions شغّل **Build Android APK** → حمّل `app-debug.apk` من الـ Artifacts وثبّته على هاتفك

**ب) محليًا بـ Android Studio:**
```bash
# 1) ابنِ الويب بوضع الموبايل (مع رابط API الحقيقي)
cd apps/web
NEXT_PUBLIC_API_URL=https://your-api NEXT_PUBLIC_WS_URL=https://your-api BUILD_TARGET=mobile npm run build
# 2) زامِن وافتح
cd ../mobile
npm install
npx cap sync android
npx cap open android   # ثم Build > Build APK في Android Studio
```

## ملاحظات
- `appId`: ‏`com.cryptoai.signals` — غيّره في `capacitor.config.ts` قبل النشر على Play Store.
- نسخة Play Store تحتاج AAB موقّعًا ‏(`./gradlew bundleRelease` + keystore) وحساب مطوّر ‏($25 مرة واحدة).
- إشعارات Push ‏(FCM) ليست مفعّلة بعد — التنبيهات الحالية Telegram/Email عبر الـ Worker. إضافة FCM لاحقًا: ‏`@capacitor/push-notifications` + جدول توكنات + إرسال من الـ Worker.
- التطبيق يحتاج الـ API منشورًا ومتاحًا من الإنترنت ‏(HTTPS مفضّل؛ أندرويد يمنع HTTP غير المشفر افتراضيًا).
