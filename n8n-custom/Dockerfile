FROM n8nio/n8n:latest

USER root
# Pre-create the directory so it's owned by node, not root (from volume mount)
RUN mkdir -p /home/node/.cache/n8n/public

# Copy the icon
COPY solid-icon.png /home/node/.cache/n8n/public/apple-touch-icon.png
COPY solid-icon.png /home/node/.cache/n8n/public/apple-touch-icon-precomposed.png
COPY solid-icon.png /home/node/.cache/n8n/public/favicon.png

# Fix permissions
RUN chown -R node:node /home/node/.cache

# Mimic Open WebUI: Empty manifest and implicit file discovery (no HTML tags)
RUN echo '{}' > /home/node/.cache/n8n/public/manifest.json

USER node

USER node
