FROM debian:bullseye-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    calibre \
    cron \
    python3 \
    python3-pip \
    python3-dev \
    git \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for web UI
RUN pip3 install --no-cache-dir \
    flask \
    flask-basicauth \
    apscheduler \
    gitpython \
    requests \
    gunicorn

# Create calibre user
RUN useradd -ms /bin/bash calibre

# Create necessary directories
RUN mkdir -p /opt/library /opt/recipes /var/log/news_server /opt/webui /opt/webui/templates \
    && chown -R calibre:calibre /opt/library /opt/recipes /var/log/news_server /opt/webui

# Copy scripts
COPY entrypoint.sh /opt/entrypoint.sh
COPY setup_cron.sh /opt/setup_cron.sh
COPY download_news.sh /opt/download_news.sh
COPY entrypoint_with_webui.sh /opt/entrypoint_with_webui.sh
COPY webui.py /opt/webui/app.py

# Copy web UI templates
COPY templates/base.html /opt/webui/templates/base.html
COPY templates/index.html /opt/webui/templates/index.html

# Set executable permissions
RUN chmod +x /opt/entrypoint.sh /opt/setup_cron.sh /opt/download_news.sh /opt/entrypoint_with_webui.sh

# Set default environment variables
ENV LIBRARY_FOLDER=/opt/library \
    RECIPES_FOLDER=/opt/recipes \
    USER_DB=/opt/users.sqlite \
    CALIBRE_USER=admin \
    CALIBRE_PASSWORD=admin \
    LOG_DIR=/var/log/news_server \
    FLASK_SECRET_KEY=change_me_in_production

# Expose Calibre server port and Web UI port
EXPOSE 8080 5000

# Set entrypoint
ENTRYPOINT ["/opt/entrypoint_with_webui.sh"]
