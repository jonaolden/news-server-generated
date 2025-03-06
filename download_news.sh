#!/bin/bash
set -e

# Source environment variables if needed
if [ -z "$LIBRARY_FOLDER" ] || [ -z "$RECIPES_FOLDER" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Environment variables not set"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Starting news download"

# Process all recipe files
for recipe in "$RECIPES_FOLDER"/*.recipe; do
    if [ -f "$recipe" ]; then
        recipe_name=$(basename "$recipe" .recipe)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Processing recipe: $recipe_name"
        
        # Run ebook-convert to fetch the news
        ebook-convert "$recipe" "$LIBRARY_FOLDER/$recipe_name.epub" \
            --output-profile=tablet \
            --pubdate=$(date +%Y-%m-%d) \
            --title="$recipe_name - $(date +%Y-%m-%d)" \
            --series="$recipe_name" \
            --series-index=$(date +%Y%m%d)
            
        if [ $? -eq 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Successfully downloaded $recipe_name"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Failed to download $recipe_name"
        fi
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] News download completed"
