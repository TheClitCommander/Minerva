# 🖥️ Minerva Desktop Launcher Guide

Your Minerva AI Assistant now has a beautiful desktop launcher! 

## 📍 **What Was Created**

✅ **Desktop App**: `Minerva AI.app` on your Desktop  
✅ **Launch Options**: 5 different ways to start Minerva  
✅ **Native macOS Integration**: Proper .app bundle with dialogs  

## 🚀 **How to Use**

### Simple Launch
1. **Double-click** `Minerva AI.app` on your Desktop
2. **Choose your option** from the dialog:
   - 🚀 **Quick Test Launcher** - Interactive menu (recommended)
   - 💬 **AI Chat (Simulation)** - Direct chat interface
   - 🌐 **Web Server** - Start web interface
   - 📊 **System Status** - Check system health
   - 🔧 **Advanced Terminal** - Full command access

3. **Terminal opens** with your chosen Minerva mode

### Launch Options Explained

| Option | What It Does | Best For |
|--------|-------------|----------|
| 🚀 Quick Test Launcher | Opens the interactive menu | First-time users, testing |
| 💬 AI Chat | Direct AI conversation | Quick AI interactions |
| 🌐 Web Server | Web interface at localhost:5000 | Browser-based usage |
| 📊 System Status | Shows component health | Troubleshooting |
| 🔧 Advanced Terminal | Full command line access | Power users |

## 🎨 **Customizing the Icon**

### Option 1: Drag & Drop
1. Right-click `Minerva AI.app` → **Get Info**
2. Find a nice icon image (PNG, JPEG, etc.)
3. Drag it to the icon area at the top of the Info window

### Option 2: Professional .icns File
1. Create or download a `.icns` file
2. Name it `icon.icns`
3. Replace the file in `Minerva AI.app/Contents/Resources/`

## 🔒 **First Time Setup**

When you first run the app, macOS might show a security warning:

### If Blocked:
1. **Right-click** the app → **Open** (instead of double-click)
2. Click **Open** in the security dialog
3. Or go to **System Preferences** → **Security & Privacy** → Click **Allow**

### Alternative:
```bash
# Remove quarantine attribute (run once)
xattr -rd com.apple.quarantine ~/Desktop/Minerva\ AI.app
```

## 🛠️ **Troubleshooting**

### App Won't Start
- Make sure you're connected to the internet for first launch
- Try right-click → Open instead of double-click
- Check Terminal for error messages

### Wrong Directory Error
- The app is configured for `/Users/bendickinson/Desktop/Minerva`
- If you moved Minerva, edit the path in the app's executable

### Want to Change the Path?
Edit: `Minerva AI.app/Contents/MacOS/Minerva AI`
Change line: `MINERVA_DIR="/Users/bendickinson/Desktop/Minerva"`

## 🎯 **Pro Tips**

- **Add to Dock**: Drag the app to your Dock for quick access
- **Keyboard Shortcut**: Use Spotlight (Cmd+Space) → type "Minerva"
- **Quick Status**: Use the 📊 System Status option to check if everything's working
- **Development**: Use 🔧 Advanced Terminal for full development access

## 📱 **What's Next**

Your Minerva system is now fully accessible from your desktop! The app provides:

✅ **Native macOS experience** with proper dialogs  
✅ **Multiple launch modes** for different use cases  
✅ **No command-line knowledge required** for basic usage  
✅ **Still full terminal access** for advanced features  

**Enjoy your desktop-integrated Minerva AI Assistant!** 🌟

---

*Created by the Minerva refactoring process - v2.0* 