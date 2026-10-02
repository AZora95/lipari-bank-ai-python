# Giorno 10: `opencode serve` in un container, la stessa versione del portatile
FROM node:22-bookworm-slim
ARG OPENCODE_VERSION=1.18.30
RUN npm install --global opencode-ai@${OPENCODE_VERSION} && npm cache clean --force
# il progetto di opencode: opencode.json e l'agente liparibank arrivano dal compose, in sola lettura
WORKDIR /workspace
EXPOSE 4096
CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]
