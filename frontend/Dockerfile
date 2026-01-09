# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build arguments
ARG REACT_APP_API_URL
ARG REACT_APP_WS_URL
ARG REACT_APP_MAPBOX_TOKEN

ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_WS_URL=${REACT_APP_WS_URL}
ENV REACT_APP_MAPBOX_TOKEN=${REACT_APP_MAPBOX_TOKEN}

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
