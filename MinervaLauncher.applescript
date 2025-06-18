-- Minerva AI Desktop Launcher
-- Save this as an Application in Script Editor

-- Get the directory where this script is located
tell application "Finder"
    set scriptPath to (path to me) as string
    set scriptFolder to (container of (scriptPath as alias)) as string
    set posixPath to POSIX path of scriptFolder
end tell

-- Display launch options
set launchChoice to choose from list {"🚀 Quick Test Launcher", "💬 AI Chat (Simulation)", "🌐 Web Server", "📊 System Status", "🔧 Advanced Options"} with title "Minerva AI Assistant" with prompt "Choose how to launch Minerva:" default items {"🚀 Quick Test Launcher"}

if launchChoice is false then
    return -- User canceled
end if

set chosenOption to item 1 of launchChoice

-- Launch Terminal and execute the appropriate command
tell application "Terminal"
    activate
    
    if chosenOption is "🚀 Quick Test Launcher" then
        do script "cd '" & posixPath & "' && python3 test_minerva.py"
    else if chosenOption is "💬 AI Chat (Simulation)" then
        do script "cd '" & posixPath & "' && python3 bin/launch_minerva.py ai"
    else if chosenOption is "🌐 Web Server" then
        do script "cd '" & posixPath & "' && echo 'Starting Minerva Web Server...' && python3 bin/launch_minerva.py server"
    else if chosenOption is "📊 System Status" then
        do script "cd '" & posixPath & "' && python3 bin/launch_minerva.py status && echo '' && echo 'Press any key to close...' && read"
    else if chosenOption is "🔧 Advanced Options" then
        do script "cd '" & posixPath & "' && echo 'Minerva AI Assistant - Advanced Options' && echo '' && echo 'Available commands:' && echo '  python3 test_minerva.py           - Interactive launcher' && echo '  python3 bin/launch_minerva.py ai  - AI Chat' && echo '  python3 bin/launch_minerva.py server - Web Server' && echo '  python3 bin/launch_minerva.py status - System Status' && echo '' && echo 'Choose your command:' && exec /bin/bash"
    end if
end tell 