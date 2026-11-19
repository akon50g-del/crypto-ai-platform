import type { CapacitorConfig } from '@capacitor/cli';

// The app bundles the static export of apps/web (out/) and talks to the
// deployed API. Set NEXT_PUBLIC_API_URL at web-build time to your server.
const config: CapacitorConfig = {
  appId: 'com.cryptoai.signals',
  appName: 'Crypto AI Signals',
  webDir: '../web/out',
  backgroundColor: '#0b0e13',
  android: { allowMixedContent: false },
  server: { androidScheme: 'https' },
};

export default config;
