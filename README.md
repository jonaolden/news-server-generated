# News Server

A Docker-based news server using Calibre to download and serve news articles, with an intuitive web interface for management.

## Features

- **Calibre Integration**: Automatically downloads news from various sources using Calibre recipes
- **Web Interface**: Easily manage your recipes and downloads through a user-friendly web UI
- **GitHub Import**: Import recipes directly from GitHub repositories
- **Scheduling**: Configure and manage download schedules through the web interface
- **User Authentication**: Secure access to both the Calibre server and management interface

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

3. Create a .env file from the example:
   ```bash
   cp .env.example .env
   ```
   
4. Edit the .env file to customize your settings:
   ```bash
   # Set a secure password
   nano .env
   ```

5. Build and start the container:
   ```bash
   docker-compose up -d
   ```

6. Access your services:
   - **Calibre Server**: http://localhost:8080
   - **Management UI**: http://localhost:5000
   - Username: admin
   - Password: (value from docker-compose.yml)

## Web Management Interface

The Web UI provides a simple and intuitive interface to manage your news server:

### Recipe Management
- View all available recipes
- Enable/disable individual recipes
- Run individual recipes on demand
- Run all enabled recipes at once

### GitHub Integration
- Import recipes directly from GitHub repositories
- Just paste the repository URL and the system will import all .recipe files

### Schedule Configuration
- Configure the download schedule using cron syntax
- Trigger manual downloads of all enabled recipes

## Configuration

### Environment Variables

The following environment variables can be configured in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| LIBRARY_FOLDER | Path to store downloaded news | /opt/library |
| RECIPES_FOLDER | Path to store recipe files | /opt/recipes |
| USER_DB | Path to the user database | /opt/users.sqlite |
| CALIBRE_USER | Default admin username | admin |
| CALIBRE_PASSWORD | Default admin password | admin |
| LOG_DIR | Directory for logs | /var/log/news_server |
| FLASK_SECRET_KEY | Secret key for Flask sessions | change_me_in_production |

### Volumes

The docker-compose.yml file mounts the following volumes:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| ./library | /opt/library | Stores downloaded news files |
| ./recipes | /opt/recipes | Stores recipe files |
| ./users.sqlite | /opt/users.sqlite | User database |
| ./logs | /var/log/news_server | Log files |
| ./webui_config.json | /opt/webui_config.json | Web UI configuration |

## Creating Custom Recipes

Calibre recipes are Python scripts that tell Calibre how to download and process news sources.

If no recipes are found when the container starts, a sample BBC News recipe will be created automatically.

You can create your own recipes in two ways:

1. **Through the Web UI**:
   - Import recipes from GitHub repositories

2. **Manually**:
   - Create a new file in the `recipes` folder with a `.recipe` extension
   - Write your recipe following the [Calibre recipe format](https://manual.calibre-ebook.com/news.html)

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

## Finding Recipe Repositories

Here are some GitHub repositories with Calibre recipes you can import:

1. **Calibre Recipes Collection**: https://github.com/kovidgoyal/calibre/tree/master/recipes
2. **NiLuJe's Calibre Recipes**: https://github.com/NiLuJe/calibre-recipes

## Logs

Logs are stored in the `logs` directory:
- `news_download.log`: Main log for news downloads
- `webui_access.log`: Web UI access log
- `webui_error.log`: Web UI error log

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
tar -czf news-server-backup.tar.gz library recipes users.sqlite logs webui_config.json
```

## Troubleshooting

### No News Downloads

If no news is being downloaded:
1. Check the logs: `cat logs/news_download.log`
2. Verify your recipe files are valid
3. Try running a manual download through the Web UI

### Can't Access Web Interface

If you can't access the web interface:
1. Verify the container is running: `docker ps`
2. Check container logs: `docker-compose logs`
3. Verify ports 8080 and 5000 are not being used by another application

## License

This project is open source and available under the MIT License.
