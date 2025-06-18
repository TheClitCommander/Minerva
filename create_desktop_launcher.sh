#!/bin/bash
# Create Minerva Desktop Launcher for macOS

echo "🚀 Creating Minerva Desktop Launcher..."

# Create the .app bundle structure
APP_NAME="Minerva AI.app"
APP_DIR="$HOME/Desktop/$APP_NAME"

echo "📁 Creating application bundle structure..."
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create the Info.plist file
echo "📝 Creating Info.plist..."
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Minerva AI</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.minerva.ai.launcher</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Minerva AI</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundleSignature</key>
    <string>MNVA</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create the main executable script
echo "⚙️ Creating main executable..."
cat > "$APP_DIR/Contents/MacOS/Minerva AI" << 'EOF'
#!/bin/bash

# Get the directory where Minerva is located
MINERVA_DIR="/Users/bendickinson/Desktop/Minerva"

# Function to show options using osascript
show_options() {
    osascript << 'APPLESCRIPT'
    set launchChoice to choose from list {"🚀 Quick Test Launcher", "💬 AI Chat (Simulation)", "🌐 Web Server", "📊 System Status", "🔧 Advanced Terminal"} with title "Minerva AI Assistant" with prompt "Choose how to launch Minerva:" default items {"🚀 Quick Test Launcher"} with multiple selections allowed false

    if launchChoice is false then
        return -- User canceled
    end if

    set chosenOption to item 1 of launchChoice
    return chosenOption
APPLESCRIPT
}

# Get user choice
CHOICE=$(show_options)

if [ -z "$CHOICE" ]; then
    echo "Launch canceled by user"
    exit 0
fi

# Navigate to Minerva directory
cd "$MINERVA_DIR" || {
    osascript -e 'display dialog "Error: Cannot find Minerva directory at /Users/bendickinson/Desktop/Minerva" buttons {"OK"} default button "OK" with icon stop'
    exit 1
}

# Execute based on choice
case "$CHOICE" in
    "🚀 Quick Test Launcher")
        osascript -e 'tell application "Terminal" to do script "cd '\''/Users/bendickinson/Desktop/Minerva'\'' && python3 test_minerva.py"'
        ;;
    "💬 AI Chat (Simulation)")
        osascript -e 'tell application "Terminal" to do script "cd '\''/Users/bendickinson/Desktop/Minerva'\'' && echo '\''🤖 Starting Minerva AI Chat (Simulation Mode)...'\'' && python3 bin/launch_minerva.py ai"'
        ;;
         "🌐 Web Server")
         osascript -e 'tell application "Terminal" to do script "cd '\''/Users/bendickinson/Desktop/Minerva'\'' && echo '\''🌐 Starting Minerva Web Server...'\'' && echo '\''🌟 Cosmic UI: http://localhost:5000/portal'\'' && echo '\''📱 Simple UI: http://localhost:5000'\'' && python3 bin/launch_minerva.py server"'
        ;;
    "📊 System Status")
        osascript -e 'tell application "Terminal" to do script "cd '\''/Users/bendickinson/Desktop/Minerva'\'' && python3 bin/launch_minerva.py status && echo '\'''\'' && echo '\''Press any key to close this window...'\'' && read -n 1"'
        ;;
    "🔧 Advanced Terminal")
        osascript -e 'tell application "Terminal" to do script "cd '\''/Users/bendickinson/Desktop/Minerva'\'' && echo '\''🔧 Minerva AI Assistant - Advanced Terminal'\'' && echo '\''===================================='\'' && echo '\''Available commands:'\'' && echo '\''  python3 test_minerva.py              - Interactive launcher'\'' && echo '\''  python3 bin/launch_minerva.py ai     - AI Chat'\'' && echo '\''  python3 bin/launch_minerva.py server - Web Server'\'' && echo '\''  python3 bin/launch_minerva.py status - System Status'\'' && echo '\''  python3 tests/test_refactored_components.py - Run tests'\'' && echo '\'''\'' && echo '\''Type your command or type '\''exit'\'' to close:'\'' && exec /bin/bash"'
        ;;
esac
EOF

# Make the executable script executable
chmod +x "$APP_DIR/Contents/MacOS/Minerva AI"

# Create a simple icon (text-based, you can replace with a real icon later)
echo "🎨 Creating icon..."
cat > "$APP_DIR/Contents/Resources/create_icon.py" << 'EOF'
#!/usr/bin/env python3
import os
from pathlib import Path

# Create a simple text-based icon
icon_text = """🌟 
AI"""

# For now, we'll create a simple placeholder
# You can replace this with a proper .icns file later
print("Icon placeholder created. To add a proper icon:")
print("1. Create or find a .icns file")
print("2. Name it 'icon.icns'")
print("3. Place it in the Resources folder")
EOF

python3 "$APP_DIR/Contents/Resources/create_icon.py"

echo ""
echo "✅ Desktop launcher created successfully!"
echo ""
echo "📍 Location: $APP_DIR"
echo ""
echo "🎯 To use:"
echo "  1. Double-click 'Minerva AI.app' on your desktop"
echo "  2. Choose your launch option from the dialog"
echo "  3. Minerva will open in Terminal"
echo ""
echo "🎨 To customize the icon:"
echo "  1. Right-click the app → Get Info"
echo "  2. Drag a new icon to the icon area at the top"
echo "  3. Or replace icon.icns in Contents/Resources/"
echo ""
echo "🔒 If macOS blocks the app:"
echo "  1. Right-click → Open (instead of double-click)"
echo "  2. Or go to System Preferences → Security & Privacy → Allow"
echo ""
echo "🚀 Ready to launch Minerva from your desktop!" 