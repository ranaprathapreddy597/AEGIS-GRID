FROM node:24-bookworm-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20 AS node-build
WORKDIR /app
RUN npm install --global pnpm@11.25.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY services/executor/package.json services/executor/package.json
RUN --mount=type=cache,id=aegis-pnpm-store,target=/pnpm/store pnpm install --frozen-lockfile --store-dir /pnpm/store
COPY apps/web apps/web
COPY services/executor services/executor
COPY packages/contracts/generated packages/contracts/generated
RUN pnpm build && pnpm test

FROM node:24-bookworm-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20 AS executor
WORKDIR /app
COPY --from=node-build /app/services/executor/dist ./dist
COPY services/executor/package.json ./package.json
USER node
CMD ["node", "dist/services/executor/src/index.js"]

FROM nginx:stable-alpine@sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94 AS web
COPY infra/local/nginx.conf /etc/nginx/nginx.conf
COPY --from=node-build /app/apps/web/dist /usr/share/nginx/html
USER nginx
ENTRYPOINT ["nginx", "-g", "daemon off;"]
