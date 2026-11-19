'use client';
import { Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/stores/auth';

function Callback() {
  const params = useSearchParams();
  const { setToken } = useAuth();
  const router = useRouter();
  useEffect(() => {
    const token = params.get('token');
    if (token) setToken(token).then(() => router.replace('/dashboard')).catch(() => router.replace('/login'));
    else router.replace('/login');
  }, [params, setToken, router]);
  return <p className="text-white/60 p-6">جارٍ إتمام تسجيل الدخول…</p>;
}

export default function Page() {
  return <Suspense><Callback /></Suspense>;
}
