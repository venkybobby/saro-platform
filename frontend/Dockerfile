FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Use node serve instead of nginx - respects $PORT automatically
FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
# serve respects $PORT env variable from Railway
CMD serve dist -l ${PORT:-3000} --single
