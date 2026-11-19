# Build context = repo root (see docker-compose.yml) so the canonical
# PostgreSQL Prisma schema can replace the local SQLite dev schema.
FROM node:22-alpine
WORKDIR /app
COPY apps/api/package*.json ./
RUN npm install
COPY apps/api/ ./
COPY prisma/schema.prisma ./prisma/schema.prisma
RUN npx prisma generate && npm run build
EXPOSE 4000
CMD ["sh", "-c", "npx prisma db push && node dist/main.js"]
