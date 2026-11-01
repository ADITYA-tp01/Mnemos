FROM node:20-alpine
WORKDIR /app
COPY .next/standalone/. .
EXPOSE 3000
ENV PORT=3000 HOSTNAME=0.0.0.0
CMD ["node", "server.js"]