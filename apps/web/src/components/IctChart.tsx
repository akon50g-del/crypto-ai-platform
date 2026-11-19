'use client';
import { useEffect, useRef } from 'react';
import { createChart, ColorType, type IChartApi, type UTCTimestamp } from 'lightweight-charts';

type Candle = { t: number; o: number; h: number; l: number; c: number; v: number };
type Lines = { entryLow?: number; entryHigh?: number; sl?: number; tp1?: number; tp2?: number };

/** Candlestick chart with ICT trade lines (entry zone / SL / TP1 / TP2).
 *  Mirrors chart_draw.py levels: only levels produced by the engine are drawn. */
export default function IctChart({ candles, lines }: { candles: Candle[]; lines?: Lines }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!ref.current || candles.length === 0) return;
    const chart = createChart(ref.current, {
      layout: { background: { type: ColorType.Solid, color: '#111418' }, textColor: '#e6e6e6' },
      grid: { vertLines: { color: '#222831' }, horzLines: { color: '#222831' } },
      width: ref.current.clientWidth, height: 380,
      timeScale: { timeVisible: true },
    });
    chartRef.current = chart;
    const series = chart.addCandlestickSeries({
      upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
      wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });
    series.setData(candles.map((c) => ({
      time: Math.floor(c.t / 1000) as UTCTimestamp,
      open: c.o, high: c.h, low: c.l, close: c.c,
    })));
    const addLine = (price: number | undefined, color: string, title: string) => {
      if (price) series.createPriceLine({ price, color, lineWidth: 1, title });
    };
    if (lines) {
      addLine(lines.entryLow, '#4fc3f7', 'Entry');
      addLine(lines.entryHigh, '#4fc3f7', 'Entry');
      addLine(lines.sl, '#ef5350', 'SL');
      addLine(lines.tp1, '#66bb6a', 'TP1');
      addLine(lines.tp2, '#66bb6a', 'TP2');
    }
    chart.timeScale().fitContent();
    const onResize = () => chart.applyOptions({ width: ref.current?.clientWidth ?? 600 });
    window.addEventListener('resize', onResize);
    return () => { window.removeEventListener('resize', onResize); chart.remove(); };
  }, [candles, lines]);

  return <div ref={ref} className="w-full rounded-xl overflow-hidden border border-line" dir="ltr" />;
}
