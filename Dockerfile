FROM node:20.19.2-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY client ./client
RUN npm run build

FROM node:20.19.2-bookworm-slim AS runtime
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund && npm cache clean --force
COPY --from=build /app/dist ./dist
COPY server ./server
COPY scripts/init-db.js scripts/sql-parser.js scripts/connect-db.js ./scripts/
COPY database ./database
USER node
EXPOSE 3000
CMD ["node", "server/index.js"]
