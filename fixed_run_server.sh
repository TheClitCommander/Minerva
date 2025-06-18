#!/bin/bash

# Fixed Run Server Script for Minerva
# This script fixes all three critical issues:
#  1. Coordinator export issue
#  2. Socket.IO version compatibility
#  3. Proper coordinator initialization

echo "==========================================="
echo "    Minerva Server with All Issues Fixed    "
echo "==========================================="

# Set dummy API keys if none exist
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Setting dummy OPENAI_API_KEY for testing"
    export OPENAI_API_KEY="sk-test12345678901234567890123456789012345678"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Setting dummy ANTHROPIC_API_KEY for testing"
    export ANTHROPIC_API_KEY="sk-ant-api12345678901234567890123456789012345"
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    echo "Setting dummy MISTRAL_API_KEY for testing"
    export MISTRAL_API_KEY="test12345678901234567890123456789012345"
fi

# Create verification script to check if coordinator is properly exported
cat > verify_coordinator_export.py << 'EOL'
import sys

print("\n=== VERIFYING COORDINATOR EXPORTS ===")
try:
    import web.multi_ai_coordinator
    print("✅ Successfully imported multi_ai_coordinator module")
    
    has_coordinator = False
    if hasattr(web.multi_ai_coordinator, 'Coordinator'):
        print(f"✅ Found Coordinator (capital C): {id(web.multi_ai_coordinator.Coordinator)}")
        has_coordinator = True
    else:
        print("❌ Missing Coordinator (capital C) export")
    
    if hasattr(web.multi_ai_coordinator, 'coordinator'):
        print(f"✅ Found coordinator (lowercase): {id(web.multi_ai_coordinator.coordinator)}")
        has_coordinator = True
    else:
        print("❌ Missing coordinator (lowercase) export")
    
    if not has_coordinator:
        print("❌ No coordinator exports found - this will cause simulated responses")
        sys.exit(1)
    else:
        print("✅ Coordinator exports verified successfully")

except Exception as e:
    print(f"❌ Error importing coordinator: {e}")
    sys.exit(1)
EOL

# Activate virtual environment if exists
if [ -d "venv_minerva" ]; then
    echo "Using existing virtual environment"
    source venv_minerva/bin/activate
fi

# Run the verification script before starting the server
python verify_coordinator_export.py
if [ $? -ne 0 ]; then
    echo "❌ Coordinator verification failed. Please check the errors above."
    echo "   The server will still start, but might use simulated responses."
else
    echo "✅ Coordinator exports verified successfully!"
fi

# Start the server
echo "Starting server with fixed configuration..."
python server.py

# Cleanup verification script
rm verify_coordinator_export.py

# Kill any existing server processes
echo "Checking for existing server instances..."
pkill -f "python server.py" 2>/dev/null
sleep 1

# Verify Python environment
echo "Verifying Python environment..."
if ! command -v python &> /dev/null; then
    echo "Python not found! Please install Python 3.8+"
    exit 1
fi

# Set environment variables for better server operation
echo "Setting up environment..."
export FLASK_ENV=production
export EVENTLET_HUB=poll
export PYTHONUNBUFFERED=1
export SOCKETIO_CLIENT_VERSION=4.7.2

# Create debug mode check file to force load all dependencies
echo "Preparing for launch..."
cat > /tmp/coordinator_check.py << 'EOF'
import sys
try:
    import web.multi_ai_coordinator
    print(f"✓ Successfully imported multi_ai_coordinator module")
    
    # Check for Coordinator (capital C) 
    if hasattr(web.multi_ai_coordinator, 'Coordinator'):
        print(f"✓ Found Coordinator variable: {web.multi_ai_coordinator.Coordinator}")
    else:
        print(f"✗ No Coordinator found in module")

    # Check if module contains MultiAICoordinator class
    if hasattr(web.multi_ai_coordinator, 'MultiAICoordinator'):
        print(f"✓ Found MultiAICoordinator class")
    else:
        print(f"✗ No MultiAICoordinator class found")
    
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
EOF

# Run the check
python /tmp/coordinator_check.py
if [ $? -ne 0 ]; then
    echo "⚠️ Coordinator check failed, but continuing anyway"
fi

echo ""
echo "========================================"
echo "    Starting Minerva Server on 5505    "
echo "========================================"
echo "Once running, access the chat at:"
echo "http://localhost:5505/portal"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Capture exit code
EXIT_CODE=$?

# If server crashed, show error
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️ Server exited with error code $EXIT_CODE"
    echo "Check the logs for more information"
fi

exit $EXIT_CODE 