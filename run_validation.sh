#!/bin/bash
# Minerva Validation and Monitoring Suite
# This script runs all validation tests and monitoring tools in sequence

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project directory
MINERVA_DIR=$(dirname "$0")
cd "$MINERVA_DIR"

# Make sure logs directory exists
mkdir -p logs

# Ensure we're in the correct Python environment
source venv/bin/activate 2>/dev/null || source minerva_env/bin/activate 2>/dev/null || echo -e "${YELLOW}⚠️ Could not activate virtual environment - using system Python${NC}"

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ ANTHROPIC_API_KEY environment variable is not set${NC}"
    echo -e "Please enter your Anthropic API key (will be used only for this session):"
    read -s API_KEY
    export ANTHROPIC_API_KEY="$API_KEY"
    echo -e "${GREEN}✅ Temporarily set ANTHROPIC_API_KEY for this session${NC}"
else
    echo -e "${GREEN}✅ Using ANTHROPIC_API_KEY from environment${NC}"
fi

echo
echo -e "${BLUE}====== MINERVA VALIDATION AND MONITORING SUITE ======${NC}"
echo

# Step 1: Run Claude-3 API diagnostic
echo -e "${CYAN}Step 1: Running Claude-3 API diagnostic...${NC}"
python claude3_diagnostic.py --api-key "$ANTHROPIC_API_KEY" --verbose
echo

# Step 2: Check if Minerva is running
echo -e "${CYAN}Step 2: Checking if Minerva is running...${NC}"
if curl -s http://127.0.0.1:13083/api/v1/health-check &>/dev/null; then
    echo -e "${GREEN}✅ Minerva is running${NC}"
else
    echo -e "${YELLOW}⚠️ Minerva does not appear to be running${NC}"
    echo -e "Would you like to start Minerva? (y/n)"
    read START_MINERVA
    if [[ "$START_MINERVA" =~ ^[Yy]$ ]]; then
        echo -e "Starting Minerva in the background..."
        nohup python minimal_test_app.py > logs/minerva_startup.log 2>&1 &
        echo -e "${GREEN}✅ Started Minerva with PID $!${NC}"
        echo -e "Waiting 5 seconds for startup..."
        sleep 5
    else
        echo -e "${RED}❌ Skipping remaining tests that require Minerva to be running${NC}"
        exit 1
    fi
fi
echo

# Step 3: Run Think Tank validation suite
echo -e "${CYAN}Step 3: Running Think Tank validation suite...${NC}"
echo -e "This will test model selection and blending performance."
python think_tank_validation.py --api-key "$ANTHROPIC_API_KEY" --output logs/validation_report_$(date +%Y%m%d_%H%M%S).json
echo

# Step 4: Run model performance monitor in test mode
echo -e "${CYAN}Step 4: Running model performance monitoring...${NC}"
echo -e "This will test multiple query types and analyze model selection patterns."
python model_performance_monitor.py --mode test --duration 30
echo

# Step 5: Check logs for Claude-3 integration
echo -e "${CYAN}Step 5: Checking logs for Claude-3 integration...${NC}"
echo -e "Recent Claude-3 related log entries:"
grep -i "claude" logs/minerva.log | tail -n 10 || echo "No Claude-related log entries found"
echo

# Summary
echo -e "${BLUE}====== VALIDATION SUMMARY ======${NC}"
echo -e "All validation tools have been executed."
echo -e "Detailed reports are available in the ${CYAN}logs/${NC} directory."
echo
echo -e "To monitor Minerva in real-time, run:"
echo -e "  ${CYAN}python model_performance_monitor.py --mode realtime --duration 300${NC}"
echo
echo -e "To test specific query types, run:"
echo -e "  ${CYAN}python think_tank_validation.py --api-key \$ANTHROPIC_API_KEY${NC}"
echo
echo -e "${GREEN}Validation complete!${NC}"
