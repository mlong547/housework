FROM node:24-alpine AS build

WORKDIR /app

RUN npm install --global --force yarn@1.22.22

COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

COPY frontend/ ./
RUN yarn build

FROM caddy:2-alpine

COPY deploy/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /usr/share/caddy
