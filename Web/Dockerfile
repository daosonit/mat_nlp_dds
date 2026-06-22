# Base image
FROM node:22

WORKDIR /app

# Copy package files to install dependencies (cached unless package.json changes)
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

EXPOSE 3000

# When code is mounted via docker-compose, this command will be overridden
# by the command specified in docker-compose.yml
CMD ["npm", "start"]
