FROM debian:bullseye-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    calibre \
    cron \
    python3 \
    python3-pip \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create calibre user
RUN useradd -ms /bin/bash calibre

# Create necessary directories
RUN mkdir -p /opt/library /opt/recipes /var/log/news_server \
    && chown -R calibre:calibre /opt/library /opt/recipes /var/log/news_server

# Copy scripts
COPY entrypoint.sh /opt/entrypoint.sh
COPY setup_cron.sh /opt/setup_cron.sh
COPY download_news.sh /opt/download_news.sh

# Set executable permissions
RUN chmod +x /opt/entrypoint.sh /opt/setup_cron.sh /opt/download_news.sh

# Set default environment variables
ENV LIBRARY_FOLDER=/opt/library \
    RECIPES_FOLDER=/opt/recipes \
    USER_DB=/opt/users.sqlite \
    CALIBRE_USER=admin \
    CALIBRE_PASSWORD=admin \
    LOG_DIR=/var/log/news_server

# Expose Calibre server port
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/opt/entrypoint.sh"]
