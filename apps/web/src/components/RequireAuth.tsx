'use client';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/stores/auth';

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, ready, loadMe } = useAuth();
  const router = useRouter();
  useEffect(() => { if (!ready) loadMe(); }, [ready, loadMe]);
  useEffect(() => { if (ready && !user) router.replace('/login'); }, [ready, user, router]);
  if (!ready || !user) return <p className="text-white/60 p-6">جارٍ التحميل…</p>;
  return <>{children}</>;
}
