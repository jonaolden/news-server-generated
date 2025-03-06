import os
import json
import re
import subprocess
import requests
import shutil
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_basicauth import BasicAuth
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import git

# Configuration
RECIPES_FOLDER = os.environ.get('RECIPES_FOLDER', '/opt/recipes')
LIBRARY_FOLDER = os.environ.get('LIBRARY_FOLDER', '/opt/library')
CONFIG_FILE = os.environ.get('CONFIG_FILE', '/opt/webui_config.json')
CRON_FILE = os.environ.get('CRON_FILE', '/etc/cron.d/news_download')

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change_me_in_production')

# Basic authentication
app.config['BASIC_AUTH_USERNAME'] = os.environ.get('CALIBRE_USER', 'admin')
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('CALIBRE_PASSWORD', 'admin')
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Helper functions
def load_config():
    """Load configuration from file or create default if not exists"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        default_config = {
            'recipes': {},
            'schedule': {
                'hour': '*/6',
                'minute': '0'
            }
        }
        save_config(default_config)
        return default_config

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=2)

def update_cron_schedule(hour, minute):
    """Update the cron schedule"""
    cron_content = f"{minute} {hour} * * * calibre bash /opt/download_news.sh\n"
    with open(CRON_FILE, 'w') as file:
        file.write(cron_content)
    subprocess.run(['systemctl', 'restart', 'cron'])

def get_recipe_info(recipe_path):
    """Extract recipe info from a recipe file"""
    info = {
        'name': os.path.basename(recipe_path).replace('.recipe', ''),
        'enabled': True,
        'last_run': None
    }
    
    try:
        with open(recipe_path, 'r') as file:
            content = file.read()
            # Extract title if found
            title_match = re.search(r'title\s*=\s*[\'"](.+?)[\'"]', content)
            if title_match:
                info['title'] = title_match.group(1)
            else:
                info['title'] = info['name']
                
            # Extract description if found
            desc_match = re.search(r'description\s*=\s*[\'"](.+?)[\'"]', content)
            if desc_match:
                info['description'] = desc_match.group(1)
            else:
                info['description'] = ''
    except Exception as e:
        app.logger.error(f"Error reading recipe {recipe_path}: {str(e)}")
        info['title'] = info['name']
        info['description'] = 'Error reading recipe'
        
    return info

def scan_recipes():
    """Scan for recipes and update config"""
    config = load_config()
    recipes = {}
    
    # Scan recipes directory
    for filename in os.listdir(RECIPES_FOLDER):
        if filename.endswith('.recipe'):
            recipe_path = os.path.join(RECIPES_FOLDER, filename)
            recipe_name = filename.replace('.recipe', '')
            
            # Get or create recipe config
            if recipe_name in config['recipes']:
                recipes[recipe_name] = config['recipes'][recipe_name]
            else:
                recipes[recipe_name] = get_recipe_info(recipe_path)
                
    # Update config
    config['recipes'] = recipes
    save_config(config)
    return config

def download_single_recipe(recipe_name):
    """Download news for a single recipe"""
    recipe_path = os.path.join(RECIPES_FOLDER, f"{recipe_name}.recipe")
    output_path = os.path.join(LIBRARY_FOLDER, f"{recipe_name}.epub")
    
    if not os.path.exists(recipe_path):
        return False, "Recipe file not found"
    
    cmd = [
        'ebook-convert',
        recipe_path,
        output_path,
        '--output-profile=tablet',
        f'--pubdate={datetime.now().strftime("%Y-%m-%d")}',
        f'--title={recipe_name} - {datetime.now().strftime("%Y-%m-%d")}',
        f'--series={recipe_name}',
        f'--series-index={datetime.now().strftime("%Y%m%d")}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Update last run time
            config = load_config()
            if recipe_name in config['recipes']:
                config['recipes'][recipe_name]['last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_config(config)
            return True, "Success"
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def download_all_recipes():
    """Download all enabled recipes"""
    config = load_config()
    results = {}
    
    for name, recipe in config['recipes'].items():
        if recipe.get('enabled', True):
            success, message = download_single_recipe(name)
            results[name] = {
                'success': success,
                'message': message
            }
    
    return results

def clone_github_repo(repo_url, target_dir=None):
    """Clone or pull a GitHub repository containing recipes"""
    try:
        # Parse the URL to get the repo name
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            return False, "Invalid GitHub repository URL"
        
        repo_name = path_parts[-1]
        if target_dir is None:
            target_dir = os.path.join('/tmp', repo_name)
        
        # Clone or pull the repository
        if os.path.exists(target_dir):
            repo = git.Repo(target_dir)
            repo.remotes.origin.pull()
            action = "Updated"
        else:
            git.Repo.clone_from(repo_url, target_dir)
            action = "Cloned"
            
        return True, f"{action} repository {repo_name} successfully"
    except Exception as e:
        return False, f"Error accessing repository: {str(e)}"

def import_recipes_from_dir(source_dir):
    """Import recipes from a directory to the recipes folder"""
    results = {
        'total': 0,
        'imported': 0,
        'skipped': 0,
        'details': []
    }
    
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.recipe'):
                results['total'] += 1
                source_path = os.path.join(root, file)
                target_path = os.path.join(RECIPES_FOLDER, file)
                
                try:
                    # Check if we should overwrite
                    if os.path.exists(target_path):
                        # Compare content
                        with open(source_path, 'r') as src_file, open(target_path, 'r') as tgt_file:
                            if src_file.read() == tgt_file.read():
                                results['skipped'] += 1
                                results['details'].append(f"Skipped {file} (identical)")
                                continue
                    
                    # Copy the recipe
                    shutil.copy2(source_path, target_path)
                    results['imported'] += 1
                    results['details'].append(f"Imported {file}")
                except Exception as e:
                    results['details'].append(f"Error importing {file}: {str(e)}")
                    
    # Rescan recipes
    scan_recipes()
    return results


# Routes
@app.route('/')
@basic_auth.required
def index():
    """Main page showing all recipes and configuration"""
    config = scan_recipes()
    return render_template('index.html', 
                          recipes=config['recipes'], 
                          schedule=config['schedule'])

@app.route('/recipes')
@basic_auth.required
def list_recipes():
    """API - List all recipes"""
    config = scan_recipes()
    return jsonify(config['recipes'])

@app.route('/recipe/<name>/toggle', methods=['POST'])
@basic_auth.required
def toggle_recipe(name):
    """Toggle a recipe on/off"""
    config = load_config()
    if name in config['recipes']:
        config['recipes'][name]['enabled'] = not config['recipes'][name].get('enabled', True)
        save_config(config)
        return jsonify({'success': True, 'enabled': config['recipes'][name]['enabled']})
    return jsonify({'success': False, 'error': 'Recipe not found'})

@app.route('/recipe/<name>/run', methods=['POST'])
@basic_auth.required
def run_recipe(name):
    """Run a single recipe"""
    success, message = download_single_recipe(name)
    return jsonify({'success': success, 'message': message})

@app.route('/run-all', methods=['POST'])
@basic_auth.required
def run_all():
    """Run all enabled recipes"""
    results = download_all_recipes()
    return jsonify(results)

@app.route('/schedule', methods=['POST'])
@basic_auth.required
def update_schedule():
    """Update the schedule"""
    hour = request.form.get('hour', '*/6')
    minute = request.form.get('minute', '0')
    
    # Update config
    config = load_config()
    config['schedule']['hour'] = hour
    config['schedule']['minute'] = minute
    save_config(config)
    
    # Update cron
    try:
        update_cron_schedule(hour, minute)
        flash('Schedule updated successfully')
    except Exception as e:
        flash(f'Error updating schedule: {str(e)}')
    
    return redirect(url_for('index'))

@app.route('/github/import', methods=['POST'])
@basic_auth.required
def github_import():
    """Import recipes from GitHub"""
    repo_url = request.form.get('repo_url', '')
    if not repo_url:
        return jsonify({'success': False, 'message': 'Repository URL is required'})
    
    # Clone the repository
    success, message = clone_github_repo(repo_url)
    if not success:
        return jsonify({'success': False, 'message': message})
    
    # Import recipes
    repo_name = urlparse(repo_url).path.strip('/').split('/')[-1]
    target_dir = os.path.join('/tmp', repo_name)
    results = import_recipes_from_dir(target_dir)
    
    return jsonify({
        'success': True,
        'message': message,
        'import_results': results
    })

# Templates
@app.template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime string"""
    if not value:
        return 'Never'
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(format)
    except:
        return value

# Main
if __name__ == '__main__':
    # Ensure config exists
    load_config()
    
    # Scan recipes on startup
    scan_recipes()
    
    # Start the app
    app.run(host='0.0.0.0', port=5000, debug=True)
