import type { Metadata, Viewport } from 'next';
import Nav from '@/components/Nav';
import ServiceWorker from '@/components/ServiceWorker';
import { DISCLAIMER } from '@/lib/api';
import './globals.css';

export const metadata: Metadata = {
  title: 'Crypto AI Signals — إشارات ICT/SMC ذكية',
  description: 'منصة تحليل عملات رقمية بمنهجية ICT/SMC مع توصيات حية وتنبيهات.',
  manifest: '/manifest.webmanifest',
  icons: { icon: '/icon-192.png', apple: '/apple-touch-icon.png' },
  appleWebApp: { capable: true, title: 'AI Signals', statusBarStyle: 'black-translucent' },
};

export const viewport: Viewport = {
  themeColor: '#0b0e13',
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <ServiceWorker />
        <Nav />
        <main className="max-w-6xl mx-auto px-4 py-6 pb-24 md:pb-10">{children}</main>
        <footer className="border-t border-line py-6 text-center text-white/40 text-sm px-4">
          <p>{DISCLAIMER}</p>
          <p className="mt-1">Crypto AI Signals © 2026</p>
        </footer>
      </body>
    </html>
  );
}
