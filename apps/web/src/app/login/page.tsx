'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { API_URL } from '@/lib/api';
import { useAuth } from '@/stores/auth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');
  const { login } = useAuth();
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr('');
    try { await login(email, password); router.push('/dashboard'); }
    catch (e: any) { setErr(e.message); }
  }

  return (
    <div className="max-w-md mx-auto card mt-8">
      <h1 className="text-2xl font-bold">تسجيل الدخول</h1>
      <form onSubmit={submit} className="space-y-3 mt-4">
        <div><label className="label">البريد الإلكتروني</label>
          <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></div>
        <div><label className="label">كلمة المرور</label>
          <input className="input" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></div>
        {err && <p className="text-down text-sm">{err}</p>}
        <button className="btn btn-primary w-full">دخول</button>
      </form>
      <a href={`${API_URL}/auth/google`} className="btn btn-ghost w-full mt-3">الدخول عبر Google</a>
      <p className="text-white/50 text-sm mt-4 text-center">ليس لديك حساب؟ <Link href="/register" className="text-accent">أنشئ حسابًا</Link></p>
      <p className="text-white/40 text-xs mt-2 text-center">تجريبي: demo@example.com / demo-password-123</p>
    </div>
  );
}
