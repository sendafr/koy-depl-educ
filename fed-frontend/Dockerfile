# --- Stage 1: Build ---
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# --- CRITICAL FIX START ---
# Accept VITE_API_URL as a build argument from the CI/CD platform (Koyeb)
ARG VITE_API_URL
# Set it as an environment variable so Vite can read it during the build
ENV VITE_API_URL=$VITE_API_URL
# --- CRITICAL FIX END ---

# Build the application (Vite will now see the correct URL)
RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf  

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]