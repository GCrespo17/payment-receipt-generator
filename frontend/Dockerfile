FROM node:22-bookworm-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --include=optional

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY . .
RUN npm run build


FROM node:22-bookworm-slim AS runtime

WORKDIR /app

RUN npm install --global serve

COPY --from=build /app/dist ./dist

ENV PORT=10000

EXPOSE 10000

CMD ["sh", "-c", "serve -s dist -l ${PORT:-10000}"]
