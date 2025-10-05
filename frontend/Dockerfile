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

# Copiamos el template para que el entrypoint oficial haga envsubst
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

# Copiamos el build de Vite
COPY --from=build /app/dist /usr/share/nginx/html

# No fijes puertos manualmente; Render inyecta $PORT y Nginx escuchará ahí
CMD ["nginx","-g","daemon off;"]
