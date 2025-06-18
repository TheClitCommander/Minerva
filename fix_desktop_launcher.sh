#!/bin/bash

# Fix Desktop Launcher Script

APP_DIR="$HOME/Desktop/Minerva AI.app"

echo "🔧 Fixing desktop launcher..."

# Create the corrected executable script
cat > "$APP_DIR/Contents/MacOS/Minerva AI" << 'EOF'
#!/bin/bash

# Simple Minerva Desktop Launcher

# Get the directory where Minerva is located
MINERVA_DIR="/Users/bendickinson/Desktop/Minerva"

# Navigate to Minerva directory
cd "$MINERVA_DIR" || {
    echo "Error: Cannot find Minerva directory"
    exit 1
}

# Show simple dialog and launch
choice=$(osascript -e '
set choices to {"🚀 Test Launcher", "🌟 Cosmic UI", "💬 AI Chat", "📊 Status"}
set selected to choose from list choices with title "Minerva AI" with prompt "Choose launch option:"
if selected is false then
    return ""
else
    return item 1 of selected
end if
')

case "$choice" in
    "🚀 Test Launcher")
        open -a Terminal
        osascript -e 'tell application "Terminal" to do script "cd /Users/bendickinson/Desktop/Minerva && python3 test_minerva.py"'
        ;;
    "🌟 Cosmic UI")
        open -a Terminal
        osascript -e 'tell application "Terminal" to do script "cd /Users/bendickinson/Desktop/Minerva && python3 launch_ui.py"'
        ;;
    "💬 AI Chat")
        open -a Terminal
        osascript -e 'tell application "Terminal" to do script "cd /Users/bendickinson/Desktop/Minerva && python3 bin/launch_minerva.py ai"'
        ;;
    "📊 Status")
        open -a Terminal
        osascript -e 'tell application "Terminal" to do script "cd /Users/bendickinson/Desktop/Minerva && python3 bin/launch_minerva.py status && read -p \"Press Enter to close...\""'
        ;;
    *)
        echo "Launch cancelled"
        ;;
esac
EOF

# Make executable
chmod +x "$APP_DIR/Contents/MacOS/Minerva AI"

echo "✅ Desktop launcher fixed!"
echo "🎯 Try double-clicking 'Minerva AI.app' on your desktop now." 