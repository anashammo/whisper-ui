FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Install Angular CLI globally
RUN npm install -g @angular/cli

# Copy application code
COPY . .

# Expose Angular dev server port
EXPOSE 4200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:4200/ || exit 1

# Start Angular dev server
CMD ["ng", "serve", "--host", "0.0.0.0", "--poll", "1000"]
