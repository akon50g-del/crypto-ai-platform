type SignalFull = {
  symbol: string; strategy: string; side: string; score: number; grade?: string | null;
  entryZoneLow: number; entryZoneHigh: number; stopLoss: number; tp1: number; tp2: number;
  rrTp1?: number | null; rrTp2?: number | null; reasonAr?: string | null;
};

const f = (n: number) => Number(n).toLocaleString('en-US', { maximumFractionDigits: 4 });

/** Arabic alert text mirroring the ICT skill output (plan + risk rules). */
export function formatSignalAlert(s: SignalFull): { title: string; body: string } {
  const title = `إشارة ${s.side} — ${s.symbol} (مسار ${s.strategy}) Score ${s.score}/10${s.grade ? ` ${s.grade}` : ''}`;
  const body = [
    title,
    `الدخول: ${f(s.entryZoneLow)} – ${f(s.entryZoneHigh)}`,
    `وقف الخسارة: ${f(s.stopLoss)}`,
    `TP1: ${f(s.tp1)}${s.rrTp1 ? ` (RR ${f(s.rrTp1)})` : ''} — أغلق 50% وانقل الوقف لنقطة التعادل`,
    `TP2: ${f(s.tp2)}${s.rrTp2 ? ` (RR ${f(s.rrTp2)})` : ''}`,
    s.reasonAr ? `السبب: ${s.reasonAr}` : '',
    'مخاطرة 1% من الرصيد، Isolated، ورافعة منخفضة. تحليل تعليمي وليس نصيحة مالية.',
  ].filter(Boolean).join('\n');
  return { title, body };
}
