#!/bin/bash
# File organization script for Minerva project

# Create backup directory for the day
BACKUP_DATE=$(date +"%Y-%m-%d")
BACKUP_DIR="/Users/bendickinson/Desktop/Minerva/versions/backups/$BACKUP_DATE"
mkdir -p "$BACKUP_DIR"

echo "Creating backup directory: $BACKUP_DIR"

# ------- ORGANIZE JAVASCRIPT FILES -------

# Chat related files - move to chat directory
echo "Organizing chat files..."
for file in /Users/bendickinson/Desktop/Minerva/web/static/js/chat*.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/minerva-chat*.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/think-tank*.js; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        # Move to chat directory
        mv "$file" "/Users/bendickinson/Desktop/Minerva/web/static/js/chat/"
    fi
done

# Core related files - move to core directory
echo "Organizing core files..."
for file in /Users/bendickinson/Desktop/Minerva/web/static/js/main.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/navigation.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/minerva-ui*.js; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        # Move to core directory
        mv "$file" "/Users/bendickinson/Desktop/Minerva/web/static/js/core/"
    fi
done

# Visualization related files - move to visualization directory
echo "Organizing visualization files..."
for file in /Users/bendickinson/Desktop/Minerva/web/static/js/planet-visualization.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/model-visualization.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/three*.js; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        # Move to visualization directory
        mv "$file" "/Users/bendickinson/Desktop/Minerva/web/static/js/visualization/"
    fi
done

# Project related files - move to projects directory
echo "Organizing project files..."
for file in /Users/bendickinson/Desktop/Minerva/web/static/js/project*.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/orb-ui/orb-ui-project.js; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        # Move to projects directory
        mv "$file" "/Users/bendickinson/Desktop/Minerva/web/static/js/projects/"
    fi
done

# Memory related files - move to memory directory
echo "Organizing memory files..."
for file in /Users/bendickinson/Desktop/Minerva/web/static/js/conversations*.js \
            /Users/bendickinson/Desktop/Minerva/web/static/js/knowledge.js; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        # Move to memory directory
        mv "$file" "/Users/bendickinson/Desktop/Minerva/web/static/js/memory/"
    fi
done

# Copy orb-ui files to visualization as they may be needed there
echo "Organizing orb-ui files..."
for file in /Users/bendickinson/Desktop/Minerva/web/static/js/orb-ui/*.js; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        # Copy to visualization directory
        cp "$file" "/Users/bendickinson/Desktop/Minerva/web/static/js/visualization/"
    fi
done

# ------- CREATE STABLE VERSIONS -------

# Create stable version of chat-core.js
echo "Creating stable versions..."
cp "/Users/bendickinson/Desktop/Minerva/web/static/js/chat/chat-core.js" "/Users/bendickinson/Desktop/Minerva/stable_builds/js/chat-core.js"
cp "/Users/bendickinson/Desktop/Minerva/web/static/js/core/zoom-manager.js" "/Users/bendickinson/Desktop/Minerva/stable_builds/js/zoom-manager.js"
cp "/Users/bendickinson/Desktop/Minerva/web/static/js/core/minerva-app.js" "/Users/bendickinson/Desktop/Minerva/stable_builds/js/minerva-app.js"

# Set stable files as read-only to prevent accidental overwriting
chmod 444 "/Users/bendickinson/Desktop/Minerva/stable_builds/js/chat-core.js"
chmod 444 "/Users/bendickinson/Desktop/Minerva/stable_builds/js/zoom-manager.js"
chmod 444 "/Users/bendickinson/Desktop/Minerva/stable_builds/js/minerva-app.js"

# ------- MOVE HTML TEST FILES TO ARCHIVE -------

echo "Archiving test HTML files..."
mkdir -p "/Users/bendickinson/Desktop/Minerva/archive/html_tests"

# Create a list of essential HTML files to keep
KEEP_FILES=(
    "/Users/bendickinson/Desktop/Minerva/web/index.html"
    "/Users/bendickinson/Desktop/Minerva/web/templates/base.html"
    "/Users/bendickinson/Desktop/Minerva/web/templates/chat.html"
    "/Users/bendickinson/Desktop/Minerva/web/templates/dashboard.html"
)

# Move all test html files to archive except those in KEEP_FILES
for file in /Users/bendickinson/Desktop/Minerva/web/*.html; do
    if [[ ! " ${KEEP_FILES[@]} " =~ " $file " ]]; then
        cp "$file" "/Users/bendickinson/Desktop/Minerva/archive/html_tests/$(basename $file)"
    fi
done

# ------- UPDATE VERSION TRACKING -------

echo "Updating version tracking..."
# Update the tracking.json file with today's date
sed -i '' "s/\"last_update\": \".*\"/\"last_update\": \"$(date +'%Y-%m-%dT%H:%M:%S%z')\"/" /Users/bendickinson/Desktop/Minerva/versions/tracking.json

# Add a newbuild entry to tracking.json
cat <<EOT >> /Users/bendickinson/Desktop/Minerva/versions/tracking.json
,
  "versions": [
    {
      "date": "$BACKUP_DATE",
      "description": "File system reorganization and clean-up",
      "changes": [
        "Reorganized all JavaScript files into structured directories",
        "Created stable builds with read-only protection",
        "Archived test HTML files",
        "Unified chat system into a single source of truth"
      ]
    }
  ]
EOT

echo "Organization complete!"
