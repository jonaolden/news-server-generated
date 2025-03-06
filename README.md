# News Server

A Docker-based news server using Calibre to download and serve news articles.

## Features

- Automatically downloads news from various sources using Calibre recipes
- Serves news articles through Calibre's built-in server
- Configurable through environment variables
- Automatic periodic downloads through cron jobs
- User authentication for accessing content

## Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/jonaolden/news-server-generated.git
   cd news-server-generated
   ```

2. Create local directories for persistent storage:
   ```bash
   mkdir -p library recipes logs
   ```

3. Customize your password in docker-compose.yml (default is "yourpassword")

4. Build and start the container:
   ```bash
   docker-compose up -d
   ```

5. Access your news server at http://localhost:8080
   - Username: admin
   - Password: (value from docker-compose.yml)

## Configuration

### Environment Variables

The following environment variables can be configured in the docker-compose.yml file:

| Variable | Description | Default |
|----------|-------------|---------|
| LIBRARY_FOLDER | Path to store downloaded news | /opt/library |
| RECIPES_FOLDER | Path to store recipe files | /opt/recipes |
| USER_DB | Path to the user database | /opt/users.sqlite |
| CALIBRE_USER | Default admin username | admin |
| CALIBRE_PASSWORD | Default admin password | admin |
| LOG_DIR | Directory for logs | /var/log/news_server |

### Volumes

The docker-compose.yml file mounts the following volumes:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| ./library | /opt/library | Stores downloaded news files |
| ./recipes | /opt/recipes | Stores recipe files |
| ./users.sqlite | /opt/users.sqlite | User database |
| ./logs | /var/log/news_server | Log files |

## Creating Custom Recipes

Calibre recipes are Python scripts that tell Calibre how to download and process news sources.

If no recipes are found when the container starts, a sample BBC News recipe will be created automatically.

To create your own recipe:

1. Create a new file in the `recipes` folder with a `.recipe` extension
2. Write your recipe following the [Calibre recipe format](https://manual.calibre-ebook.com/news.html)

Example recipe structure:

```python
#!/usr/bin/env python
from calibre.web.feeds.news import BasicNewsRecipe

class MyNewsSource(BasicNewsRecipe):
    title = 'My News Source'
    __author__ = 'Your Name'
    description = 'Description of the news source'
    oldest_article = 1  # Days
    max_articles_per_feed = 25
    language = 'en'
    
    feeds = [
        ('Section 1', 'http://example.com/feed1.xml'),
        ('Section 2', 'http://example.com/feed2.xml'),
    ]
```

## Logs

Logs are stored in the `logs` directory, with the main log file being `news_download.log`.

You can view the logs with:
```bash
cat logs/news_download.log
```

## Maintenance

### Updating

To update to a new version:

```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup

To backup your data:

```bash
tar -czf news-server-backup.tar.gz library recipes users.sqlite logs
```

## Troubleshooting

### No News Downloads

If no news is being downloaded:

1. Check the logs: `cat logs/news_download.log`
2. Verify your recipe files are valid
3. Try running a manual download:
   ```bash
   docker exec -it news-server-generated_news-server_1 su - calibre -c "bash /opt/download_news.sh"
   ```

### Can't Access Web Interface

If you can't access the web interface:

1. Verify the container is running: `docker ps`
2. Check container logs: `docker-compose logs`
3. Verify port 8080 is not being used by another application

## License

This project is open source and available under the MIT License.
