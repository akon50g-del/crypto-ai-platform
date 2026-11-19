# Build context = repo root (see docker-compose.yml) so the canonical
# PostgreSQL Prisma schema can replace the local SQLite dev schema.
FROM node:22-alpine
WORKDIR /app
COPY services/worker/package*.json ./
RUN npm install
COPY services/worker/ ./
COPY prisma/schema.prisma ./prisma/schema.prisma
RUN npx prisma generate && npm run build
CMD ["node", "dist/index.js"]
