FROM node:20-alpine AS base

WORKDIR /app
COPY package*.json ./
RUN npm install

# ── Development ────────────────────────────────────────────────────────────────
FROM base AS development

COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── Build ──────────────────────────────────────────────────────────────────────
FROM base AS builder

ARG VITE_APP_NAME=Ximbra
ARG VITE_API_BASE_URL
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN npm run build

# ── Production ─────────────────────────────────────────────────────────────────
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
