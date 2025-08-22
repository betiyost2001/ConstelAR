# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app

# instala deps con lockfile si existe
COPY package*.json ./
RUN npm ci

# copia el código y construye
COPY . .
# permite pasar VITE_API_URL como build-arg
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# ---------- runtime (nginx) ----------
FROM nginx:alpine
# config SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf
# copia el build
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx","-g","daemon off;"]
