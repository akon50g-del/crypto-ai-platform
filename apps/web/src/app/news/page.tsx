'use client';
import { useEffect, useState } from 'react';
import RequireAuth from '@/components/RequireAuth';
import { api } from '@/lib/api';

function Inner() {
  const [news, setNews] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  useEffect(() => {
    api('/news').then((d) => setNews(d.news)).catch(() => {});
    api('/calendar').then((d) => setEvents(d.events)).catch(() => {});
  }, []);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold">الأخبار والتقويم</h1>
      <section>
        <h2 className="font-bold text-lg mb-3">أحداث اقتصادية قادمة</h2>
        {events.length === 0
          ? <p className="card text-white/60">لا أحداث مسجلة — تُجلب تلقائيًا في Phase 5 (News Agent). تذكّر: المحرك يوقف التنبيهات ±30 دقيقة حول الأخبار عالية التأثير.</p>
          : <div className="space-y-2">{events.map((e) => (
            <div key={e.id} className="card text-sm flex justify-between gap-2 flex-wrap">
              <span>{e.title} <span className="badge bg-down/15 text-down">{e.impact}</span></span>
              <span className="text-white/50">{new Date(e.scheduledAt).toLocaleString('ar-EG')}</span>
            </div>))}</div>}
      </section>
      <section>
        <h2 className="font-bold text-lg mb-3">أخبار الكريبتو</h2>
        {news.length === 0
          ? <p className="card text-white/60">لا أخبار بعد — تُجلب تلقائيًا في Phase 5 (News Agent).</p>
          : <div className="space-y-3">{news.map((n) => (
            <a key={n.id} href={n.url ?? '#'} target="_blank" rel="noreferrer" className="card block hover:border-accent/50">
              <p className="font-semibold">{n.titleAr ?? n.title}</p>
              <p className="text-white/50 text-xs mt-1">{n.source} · {new Date(n.publishedAt).toLocaleString('ar-EG')} · تأثير {n.impact}</p>
            </a>))}</div>}
      </section>
    </div>
  );
}

export default function Page() {
  return <RequireAuth><Inner /></RequireAuth>;
}
