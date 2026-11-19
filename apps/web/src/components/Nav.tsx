'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/stores/auth';

const LINKS = [
  { href: '/dashboard', label: 'الرئيسية' },
  { href: '/signals', label: 'التوصيات' },
  { href: '/coin/BTCUSDT', label: 'العملات' },
  { href: '/news', label: 'الأخبار' },
  { href: '/journal', label: 'السجل' },
  { href: '/settings', label: 'الإعدادات' },
];

export default function Nav() {
  const { user, ready, loadMe, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => { if (!ready) loadMe(); }, [ready, loadMe]);
  const isApp = LINKS.some((l) => pathname.startsWith(l.href.split('/')[1] ? `/${l.href.split('/')[1]}` : l.href)) || pathname.startsWith('/billing');

  return (
    <>
      <header className="sticky top-0 z-40 bg-ink/90 backdrop-blur border-b border-line">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/" className="font-bold text-lg">Crypto AI <span className="text-accent">Signals</span></Link>
          <nav className="hidden md:flex items-center gap-4 text-sm">
            {user ? LINKS.map((l) => (
              <Link key={l.href} href={l.href} className={pathname.startsWith(l.href) ? 'text-accent' : 'text-white/70 hover:text-white'}>{l.label}</Link>
            )) : (<>
              <Link href="/pricing" className="text-white/70 hover:text-white">الأسعار</Link>
              <Link href="/login" className="text-white/70 hover:text-white">دخول</Link>
              <Link href="/register" className="btn btn-primary !py-1.5">ابدأ مجانًا</Link>
            </>)}
            {user && (
              <>
                <Link href="/billing" className="badge bg-accent/15 text-accent border border-accent/40">{user.planTier}</Link>
                <button onClick={() => { logout(); router.push('/'); }} className="text-white/60 hover:text-white">خروج</button>
              </>
            )}
          </nav>
          {!user && <Link href="/login" className="md:hidden text-sm text-accent">دخول</Link>}
        </div>
      </header>
      {user && isApp && (
        <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-panel border-t border-line grid grid-cols-6 text-center text-[11px]">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className={`py-2.5 ${pathname.startsWith(l.href) ? 'text-accent' : 'text-white/60'}`}>{l.label}</Link>
          ))}
        </nav>
      )}
    </>
  );
}
