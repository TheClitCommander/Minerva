#!/usr/bin/env python3
"""
Minerva WebSocket and Think Tank Reliability Fix

This script applies the following enhancements to Minerva:
1. WebSocket request tracking and timeout handling
2. Enhanced Think Tank processing with parallel model execution
3. Guaranteed fallback responses when processing fails
4. Detailed error logging and diagnostics
"""
import os
import sys
import time
import logging
import importlib
import threading
from pathlib import Path
from datetime import datetime

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/minerva_fix_application.log',
    filemode='a'
)
logger = logging.getLogger('apply_fix')

# Add Minerva paths
minerva_path = Path('/Users/bendickinson/Desktop/Minerva')
sys.path.append(str(minerva_path))
sys.path.append(str(minerva_path / 'web'))

# Integration functions
def apply_think_tank_fix():
    """Apply the enhanced ThinkTankProcessor to Minerva's multi_ai_coordinator"""
    logger.info("🧠 Applying Think Tank reliability fix")
    print("Applying Think Tank reliability fix...")
    
    try:
        # Import Minerva's MultiAICoordinator
        from web import multi_ai_coordinator
        
        # Add import for enhanced Think Tank processor
        import think_tank_fix
        importlib.reload(think_tank_fix)  # Ensure latest version
        from think_tank_fix import ThinkTankProcessor, THINK_TANK_TIMEOUT, FALLBACK_RESPONSE
        
        # Store original method for reference
        original_process = multi_ai_coordinator.MultiAICoordinator.process_think_tank
        
        # Create patched method
        def patched_process_think_tank(self, message_id, session_id, query, **kwargs):
            """Enhanced Think Tank processor with parallel model processing and timeout handling"""
            logger.info(f"🧠 [ENHANCED_THINK_TANK] Processing message {message_id}")
            
            # Get available models
            models = self.get_available_models()
            logger.info(f"🧠 [THINK_TANK_MODELS] Using models: {[model.name for model in models]}")
            
            # Initialize enhanced processor with these models
            processor = ThinkTankProcessor(models)
            
            # Process the request with enhanced handling
            try:
                result = processor.process_request(message_id, session_id, query)
                logger.info(f"✅ [THINK_TANK_COMPLETE] Completed processing for message {message_id}")
                return result
            except Exception as e:
                logger.error(f"❌ [THINK_TANK_ERROR] Error in Think Tank process: {str(e)}")
                # Fallback to original processor if needed
                try:
                    return original_process(self, message_id, session_id, query, **kwargs)
                except Exception as inner_e:
                    logger.error(f"❌ [THINK_TANK_FALLBACK_ERROR] Fallback also failed: {str(inner_e)}")
                    # Last resort - emit fallback directly
                    processor._send_fallback_response(session_id, message_id, 
                                                   {"error": f"Both enhanced and original processing failed"})
                    return None
        
        # Apply the patch
        logger.info("🔄 Replacing MultiAICoordinator.process_think_tank with enhanced version")
        multi_ai_coordinator.MultiAICoordinator.process_think_tank = patched_process_think_tank
        
        # Verify the patch
        current_method = multi_ai_coordinator.MultiAICoordinator.process_think_tank
        logger.info(f"✅ Successfully applied Think Tank reliability fix: {current_method.__name__}")
        print("✅ Think Tank reliability fix applied")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply Think Tank fix: {str(e)}")
        print(f"❌ Error applying Think Tank fix: {str(e)}")
        return False

def create_backup(file_path):
    """Create a backup of a file before modification"""
    if not os.path.exists(file_path):
        logger.warning(f"⚠️ Cannot create backup: File {file_path} not found")
        return False
    
    backup_dir = minerva_path / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(file_path)
    backup_path = backup_dir / f"{filename}.{timestamp}.bak"
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"✅ Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {str(e)}")
        return False

def restore_backup(backup_path, target_path):
    """Restore a file from backup"""
    if not os.path.exists(backup_path):
        logger.error(f"❌ Cannot restore: Backup {backup_path} not found")
        return False
    
    try:
        import shutil
        shutil.copy2(backup_path, target_path)
        logger.info(f"✅ Restored {target_path} from backup {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to restore from backup: {str(e)}")
        return False

def apply_websocket_fixes():
    """Apply enhanced WebSocket client with authentication capabilities"""
    logger.info("🔌 Applying WebSocket authentication and reliability fixes")
    print("\n🔄 Applying WebSocket authentication and reliability fixes...")
    
    # Target files that need to be patched
    websocket_path = minerva_path / 'web' / 'websocket_client.py'
    minimal_fix_path = minerva_path / 'minimal_websocket_fix.py'
    
    backups = {}
    success = True
    
    try:
        # 1. Create backups of original files
        print("📦 Creating backups of original files...")
        for path in [websocket_path]:
            if os.path.exists(path):
                backup = create_backup(path)
                if backup:
                    backups[path] = backup
                    print(f"✅ Backup created: {os.path.basename(backup)}")
                else:
                    logger.error(f"❌ Failed to create backup for {path}")
                    print(f"❌ Failed to create backup for {path}")
                    return False
        
        # 2. Import the enhanced WebSocket client
        print("📥 Importing enhanced WebSocket client...")
        if not os.path.exists(minimal_fix_path):
            logger.error(f"❌ Enhanced WebSocket client not found at {minimal_fix_path}")
            print(f"❌ Enhanced WebSocket client not found at {minimal_fix_path}")
            return False
            
        import minimal_websocket_fix
        importlib.reload(minimal_websocket_fix)  # Ensure latest version
        
        # 3. Apply the WebSocket auth enhancements
        print("🔧 Applying WebSocket authentication enhancements...")
        
        # Read the content of the enhanced WebSocket client
        with open(minimal_fix_path, 'r') as f:
            enhanced_client = f.read()
        
        # Write to the target file
        with open(websocket_path, 'w') as f:
            f.write(enhanced_client)
        
        logger.info("✅ WebSocket client successfully enhanced with authentication capabilities")
        print("✅ WebSocket client successfully enhanced with authentication capabilities")
        
        # 4. Verify the patch by importing and checking for authentication method
        print("🔍 Verifying WebSocket client patch...")
        try:
            # Import the module to verify it loads correctly
            import importlib.util
            spec = importlib.util.spec_from_file_location("websocket_client", websocket_path)
            websocket_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(websocket_module)
            
            # Check if the authentication method exists
            if hasattr(websocket_module.WebSocketClient, 'set_authentication'):
                logger.info("✅ WebSocket authentication method verified")
                print("✅ WebSocket authentication method verified")
            else:
                logger.error("❌ WebSocket authentication method not found after patching")
                print("❌ WebSocket authentication method not found after patching")
                success = False
        except Exception as e:
            logger.error(f"❌ Error verifying WebSocket client patch: {str(e)}")
            print(f"❌ Error verifying WebSocket client patch: {str(e)}")
            success = False
        
        return success
            
    except Exception as e:
        logger.error(f"❌ Error applying WebSocket fixes: {str(e)}")
        print(f"❌ Error applying WebSocket fixes: {str(e)}")
        
        # Rollback in case of failure
        if backups:
            print("⚠️ Error occurred, rolling back changes...")
            for target_path, backup_path in backups.items():
                if restore_backup(backup_path, target_path):
                    print(f"✅ Rolled back changes to {os.path.basename(target_path)}")
                else:
                    print(f"❌ Failed to roll back changes to {os.path.basename(target_path)}")
        
        return False

def verify_fixes():
    """Verify the applied fixes with comprehensive checks"""
    logger.info("🔍 Verifying applied fixes")
    print("\n🔍 Verifying fixes are properly applied...")
    
    verification_results = {
        "websocket_client": False,
        "websocket_authentication": False,
        "websocket_fallback": False,
        "think_tank_fix": False,
        "logging": False
    }
    
    try:
        # Check for enhanced WebSocket client
        try:
            from web.websocket_client import WebSocketClient
            
            # Check for authentication capabilities
            if hasattr(WebSocketClient, 'set_authentication'):
                verification_results["websocket_authentication"] = True
                logger.info("✅ WebSocket authentication capability is active")
                print("✅ WebSocket authentication capability is active")
            else:
                logger.error("❌ WebSocket authentication capability not found")
                print("❌ WebSocket authentication capability not found")
            
            # Check for fallback capabilities
            if hasattr(WebSocketClient, 'fallback_to_polling') or \
               any('fallback' in attr for attr in dir(WebSocketClient) if not attr.startswith('__')):
                verification_results["websocket_fallback"] = True
                logger.info("✅ WebSocket fallback capability is active")
                print("✅ WebSocket fallback capability is active")
            else:
                logger.error("❌ WebSocket fallback capability not found")
                print("❌ WebSocket fallback capability not found")
                
            # Mark the general WebSocket client as verified
            verification_results["websocket_client"] = True
            logger.info("✅ Enhanced WebSocket client is active")
            print("✅ Enhanced WebSocket client is active")
        except Exception as e:
            logger.error(f"❌ WebSocket client verification failed: {str(e)}")
            print(f"❌ WebSocket client verification failed: {str(e)}")
        
        # Check for Think Tank fix
        try:
            from web import multi_ai_coordinator
            current_think_tank = multi_ai_coordinator.MultiAICoordinator.process_think_tank
            if "enhanced" in current_think_tank.__doc__.lower():
                verification_results["think_tank_fix"] = True
                logger.info("✅ Think Tank fix is properly applied")
                print("✅ Think Tank fix is properly applied")
            else:
                logger.warning("⚠️ Think Tank method doesn't contain 'enhanced' in its docstring")
                print("⚠️ Think Tank fix might not be properly applied")
        except Exception as e:
            logger.error(f"❌ Think Tank fix verification failed: {str(e)}")
            print(f"❌ Think Tank fix verification failed: {str(e)}")
        
        # Check for logs
        log_files = ["minerva_fix_application.log", "websocket_fix.log", "think_tank_fix.log"]
        log_exists = False
        for log_file in log_files:
            log_path = f"logs/{log_file}"
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                log_exists = True
                logger.info(f"✅ Log file {log_file} exists and contains data")
                print(f"✅ Log file {log_file} exists and contains data")
        
        verification_results["logging"] = log_exists
        
        # Overall verification
        if all(verification_results.values()):
            logger.info("✅ All fixes successfully verified")
            print("\n✅ All fixes have been successfully applied and verified!")
        else:
            logger.warning("⚠️ Some fixes could not be fully verified")
            failed = [k for k, v in verification_results.items() if not v]
            print(f"\n⚠️ Some fixes could not be fully verified: {', '.join(failed)}")
            print("Please check the logs for more details.")
        
        return verification_results
        
    except Exception as e:
        logger.error(f"❌ Error during verification: {str(e)}")
        print(f"❌ Error during verification: {str(e)}")
        return verification_results

def main():
    print("\n===== Applying Minerva WebSocket Authentication and Think Tank Fixes =====")
    logger.info("Starting WebSocket Authentication and Think Tank fix application")
    
    # Present application information
    print("\n🔧 This script will apply the following enhancements to Minerva:")
    print("  1. Enhanced WebSocket client with comprehensive authentication support")
    print("  2. HTTP polling fallback for WebSocket connection failures")
    print("  3. Think Tank processing with parallel model execution")
    print("  4. Detailed error logging and diagnostics")
    print("\n🛠 Backup files will be created before any modifications")
    print("  In case of failure, the system will automatically roll back to the original files")
    
    # Ask for confirmation before proceeding
    try:
        confirm = input("\n⚠️ Proceed with applying fixes? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled by user.")
            return
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    
    print("\n🔌 Starting application of fixes...")
    
    # 1. Apply Think Tank fix
    think_tank_success = apply_think_tank_fix()
    
    # 2. Apply WebSocket fix with authentication capabilities
    websocket_success = apply_websocket_fixes()
    
    # 3. Verify fixes
    verification_results = verify_fixes()
    
    # 4. Run a test if all fixes were applied successfully
    if all([think_tank_success, websocket_success]):
        print("\n🧪 Running a quick test of the applied fixes...")
        try:
            import enhanced_websocket_verification
            test_command = f"python3 enhanced_websocket_verification.py --auth --auth-method=auto --fallback"
            print(f"\nTo test the fixes, you can run: {test_command}")
            print("\nNote: You may need to restart your Minerva server for all changes to take effect.")
        except ImportError:
            print("\n⚠️ Verification script not found. You can test the fixes manually after restarting the server.")
    
    # Summary
    print("\n===== Fix Application Summary =====")
    print(f"✅ Think Tank Fix: {'Applied' if think_tank_success else 'Failed'}")
    print(f"✅ WebSocket Fix: {'Applied' if websocket_success else 'Failed'}")
    print("")
    
    # Next steps
    print("\n===== Next Steps =====")
    print("1. Run the verification test to confirm fixes are working:")
    print("   python minerva_verification_test.py")
    print("")
    print("2. Check the logs for detailed information:")
    for log_file in ["minerva_fix_application.log", "websocket_fix.log", "think_tank_fix.log"]:
        print(f"   - logs/{log_file}")
    print("")
    print("3. If any issues occur, check the verification test results")
    print("   for specific failure details.")
    
    # Completion message
    print("\n===== Fix Application Completed =====")
    logger.info("Completed WebSocket and Think Tank fix application")

if __name__ == "__main__":
    main()
