#!/bin/bash

# Script to reorganize the Minerva codebase by moving redundant files to delete_me_later directories
echo "Starting Minerva codebase cleanup..."

# Ensure the target directories exist
mkdir -p delete_me_later/redundant_ai
mkdir -p delete_me_later/unused_routes
mkdir -p delete_me_later/tests
mkdir -p delete_me_later/legacy_sockets
mkdir -p delete_me_later/dead_utils

# 1. Move redundant server implementations to delete_me_later/redundant_ai/
echo "Moving redundant server implementations..."
mv -v forever_run_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v forever_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v minerva_direct_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v minerva_chat_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v chat_directly.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v standalone_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v direct_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v simple_fixed_server.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v just_run_this.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v fix_everything.py delete_me_later/redundant_ai/ 2>/dev/null || true
mv -v quick_fix.py delete_me_later/redundant_ai/ 2>/dev/null || true

# 2. Move legacy shell scripts to delete_me_later/unused_routes/
echo "Moving legacy shell scripts..."
mv -v no_kill_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_minerva_direct.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_fixed_chat.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_immortal_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v monitor_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_chat_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_fixed_minerva.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_direct.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_standalone.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_fixed_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v just_run_this.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v direct_run_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v fixed_run_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v test_minerva_fixes.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_server_test.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v test_fixes.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v simple_test_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v test_api_responses.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_huggingface_test.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v start_think_tank.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_think_tank_server.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v test_apis.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_minerva_think_tank.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_with_real_apis.sh delete_me_later/unused_routes/ 2>/dev/null || true
mv -v run_server_with_api.sh delete_me_later/unused_routes/ 2>/dev/null || true

# 3. Move test HTML files to delete_me_later/tests/
echo "Moving test HTML files..."
mv -v standalone_test.html delete_me_later/tests/ 2>/dev/null || true
mv -v direct_chat_test.html delete_me_later/tests/ 2>/dev/null || true
mv -v simple-test.html delete_me_later/tests/ 2>/dev/null || true

# 4. Move test and debug files to delete_me_later/dead_utils/
echo "Moving test and debug files..."
mv -v verify_coordinator_export.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v verify_coordinator.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v debug_api_access.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v socket_io_test.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v test_websocket.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v test_huggingface.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v final_test.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v verify_think_tank.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v test_coordinator.py delete_me_later/dead_utils/ 2>/dev/null || true
mv -v socket_fix.js delete_me_later/dead_utils/ 2>/dev/null || true
mv -v ai_coordinator_singleton.py delete_me_later/dead_utils/ 2>/dev/null || true

# 5. Handle web directory files
echo "Creating backup of important web files..."
mkdir -p web/backup_files

# First, backup important files that might be used
cp -v web/multi_ai_coordinator.py web/backup_files/ 2>/dev/null || true
cp -v web/minerva_extensions.py web/backup_files/ 2>/dev/null || true
cp -v web/minerva-portal.html web/backup_files/ 2>/dev/null || true

# Create and populate legacy_sockets directory for web files
mkdir -p delete_me_later/legacy_sockets/web
mv -v web/minerva-portal-improved.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_orbital.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minimal_api.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minimal_app.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_central.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/launch_minerva.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_server.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_server.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/index.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/dashboard.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_consolidated.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_processor.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/fix-critical.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/working_server.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_central_server.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/bridge_server.log delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/dotenv_dummy.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/openai_dummy.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/pandas_dummy.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_api.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/chat-diagnostic.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/bridge-diagnostic.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/launch-test.sh delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_floating_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_chat_bridge.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/memory_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/navigation.js delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_diagnostics.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/boss_ai.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/working_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/floating_chat_solution.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/guaranteed_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/direct_solution.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/simple_working_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/projects.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/ultra_minimal.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/basic_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/model_processors.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_chat.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/ensemble_validator.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/simplified_minerva.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/orbital_simple.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/server.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_functional_ui.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_elegant_ui.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/think_tank_simple.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/open_minerva_ui.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_orbital_fixed.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/standalone_orbital_ui.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/orbital_lite.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/orbital_standalone.html delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/logging_config.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/routes.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/response_generator.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/router_integration.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/advanced_model_router.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/route_request.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/enhanced_analytics_routes.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/enhanced_analytics.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/app_no_eventlet.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/api_request_handler.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/dashboard.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/api_failure_status.json delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/hierarchical_workflow.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/free_model_config.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/multi_model_processor.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/api_verification.log delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/openai_key_check.log delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/verify_api_status.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/openai_key_check.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/model_failure_handler.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/api_key_manager.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/mock_model_processor.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/app.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/minerva_api.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true
mv -v web/huggingface_config.py delete_me_later/legacy_sockets/web/ 2>/dev/null || true

echo "Creating clean directory structure..."
# Create a clean directory structure
mkdir -p web/chat
mkdir -p web/api
mkdir -p web/ui

# Move the essential components to keep the server running
cp -v web/backup_files/multi_ai_coordinator.py web/api/ 2>/dev/null || true
cp -v web/backup_files/minerva_extensions.py web/api/ 2>/dev/null || true
cp -v web/backup_files/minerva-portal.html web/ui/ 2>/dev/null || true

# Copy enhanced_fallback.py to the api directory
cp -v web/enhanced_fallback.py web/api/ 2>/dev/null || true

echo "Cleanup complete!"
echo "Core files preserved in web/{api,ui,chat} directories"
echo "Redundant files moved to delete_me_later/ subdirectories" 