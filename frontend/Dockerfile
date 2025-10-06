# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# Si NO vas a usar VITE_API_URL en build, podés borrar estas dos líneas:
# ARG VITE_API_URL
# ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ---------- runtime (nginx) ----------
FROM nginx:alpine

# Set environment variables for nginx template
ENV API_HOST=api
ENV API_PORT=8000
ENV PORT=80

# Copiamos el template para que el entrypoint oficial haga envsubst
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

# Copiamos el build de Vite
COPY --from=build /app/dist /usr/share/nginx/html

# Debug: Log environment variables before starting nginx
CMD ["sh", "-c", "echo 'Environment variables:' && env | grep -E '(PORT|API_HOST|API_PORT)' && echo 'Starting nginx...' && nginx -g 'daemon off;'"]
