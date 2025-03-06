#!/bin/bash
set -e

# Write out current crontab
crontab -l > /tmp/current_cron 2>/dev/null || echo "# New crontab" > /tmp/current_cron

# Check if our job is already in crontab
if ! grep -q "download_news.sh" /tmp/current_cron; then
    # Add job to download news every 6 hours
    echo "0 */6 * * * bash /opt/download_news.sh >> $LOG_FILE 2>&1" >> /tmp/current_cron
    
    # Install new crontab
    crontab /tmp/current_cron
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Added news download cron job"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] News download cron job already exists"
fi

# Clean up
rm /tmp/current_cron

# Start cron service
service cron start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Started cron service"
