#!/usr/bin/env bash
# Crypto AI Signals Platform — one-command deployment on a fresh Ubuntu VPS.
# Usage (inside the project folder, as root or with sudo):
#   bash deploy.sh
# Optional: DOMAIN=example.com bash deploy.sh   (prints HTTPS next steps)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> [1/6] Installing Docker (if needed)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null

echo "==> [2/6] Generating .env with strong secrets (if missing)"
if [ ! -f .env ]; then
  PGP=$(openssl rand -base64 24 | tr -d '/+=' | head -c 28)
  JWT=$(openssl rand -hex 32)
  TOK=$(openssl rand -hex 24)
  HOST_IP=$(curl -s ifconfig.me || echo "localhost")
  cat > .env <<EOF
POSTGRES_USER=crypto
POSTGRES_PASSWORD=$PGP
POSTGRES_DB=crypto_ai
JWT_SECRET=$JWT
AI_ENGINE_INTERNAL_TOKEN=$TOK
FRONTEND_URL=http://$HOST_IP:3000
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CALLBACK_URL=http://$HOST_IP:4000/auth/google/callback
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_PRO=
STRIPE_PRICE_VIP=
TELEGRAM_BOT_TOKEN=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=signals@example.com
NEXT_PUBLIC_API_URL=http://$HOST_IP:4000
NEXT_PUBLIC_WS_URL=http://$HOST_IP:4000
BINANCE_BASE_URL=https://data-api.binance.vision
EOF
  chmod 600 .env
  echo "    .env created for host $HOST_IP"
else
  echo "    .env exists — keeping it"
fi

echo "==> [3/6] Opening firewall ports (if ufw present)"
if command -v ufw >/dev/null 2>&1; then
  ufw allow 3000/tcp >/dev/null 2>&1 || true
  ufw allow 4000/tcp >/dev/null 2>&1 || true
  ufw allow 8000/tcp >/dev/null 2>&1 || true
fi

echo "==> [4/6] Building and starting all services"
docker compose up --build -d

echo "==> [5/6] Waiting for API health"
for i in $(seq 1 30); do
  if curl -sf http://localhost:4000/health >/dev/null 2>&1; then echo "    API healthy"; break; fi
  sleep 5
  [ "$i" = "30" ] && echo "    WARNING: API not healthy yet — check: docker compose logs api"
done

echo "==> [6/6] Seeding demo data"
docker compose exec -T api npm run db:seed || echo "    seed skipped (already seeded?)"

HOST_IP=$(curl -s ifconfig.me || echo "localhost")
echo ""
echo "============================================================"
echo " DEPLOYED — Crypto AI Signals Platform"
echo "   Website : http://$HOST_IP:3000"
echo "   API docs: http://$HOST_IP:4000/docs"
echo "   Engine  : http://$HOST_IP:8000/docs"
echo "   Demo login: demo@example.com / demo-password-123"
echo ""
echo " Next (optional): domain + HTTPS via Caddy (see docs/deploy.md),"
echo " then set TELEGRAM_BOT_TOKEN / STRIPE_* / GOOGLE_* in .env and"
echo " run: docker compose up -d"
echo "============================================================"
