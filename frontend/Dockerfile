# Multi-stage Dockerfile for React Frontend
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy frontend source code and build production dist
COPY . .
RUN npm run build

# Production serve stage using Node preview or nginx
FROM node:20-alpine AS runner

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
