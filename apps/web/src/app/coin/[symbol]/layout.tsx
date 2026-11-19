// Server layout: pre-render the 8 approved symbols for static export (mobile build).
export function generateStaticParams() {
  return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT', 'DOGEUSDT', 'LINKUSDT', 'AVAXUSDT']
    .map((symbol) => ({ symbol }));
}

export default function CoinLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
