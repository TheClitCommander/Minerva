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

def apply_websocket_fixes():
    """Apply WebSocket reliability fixes to prevent stuck connections"""
    logger.info("🔌 Applying WebSocket reliability fixes")
    print("Applying WebSocket reliability fixes...")
    
    try:
        # Import the WebSocket fix
        import websocket_fix
        importlib.reload(websocket_fix)  # Ensure latest version
        
        # Apply the patch
        if websocket_fix.patch_websocket_handler():
            logger.info("✅ WebSocket handler successfully patched")
            print("✅ WebSocket reliability fix applied")
            return True
        else:
            logger.error("❌ Failed to patch WebSocket handler")
            print("❌ Failed to patch WebSocket handler")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error applying WebSocket fixes: {str(e)}")
        print(f"❌ Error applying WebSocket fixes: {str(e)}")
        return False

def verify_fixes():
    """Verify the applied fixes"""
    logger.info("🔍 Verifying applied fixes")
    print("\nVerifying fixes are properly applied...")
    
    verification_results = {
        "websocket_fix": False,
        "think_tank_fix": False,
        "logging": False
    }
    
    try:
        # Check for WebSocket fix
        try:
            from websocket_request_tracker import get_request_tracker
            tracker = get_request_tracker()
            verification_results["websocket_fix"] = True
            logger.info("✅ WebSocket request tracker is active")
            print("✅ WebSocket request tracker is active")
        except Exception as e:
            logger.error(f"❌ WebSocket request tracker verification failed: {str(e)}")
            print(f"❌ WebSocket fix verification failed: {str(e)}")
        
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
    print("\n===== Applying Minerva WebSocket and Think Tank Fixes =====")
    logger.info("Starting WebSocket and Think Tank fix application")
    
    # 1. Apply Think Tank fix
    think_tank_success = apply_think_tank_fix()
    
    # 2. Apply WebSocket fix
    websocket_success = apply_websocket_fixes()
    
    # 3. Verify fixes
    verification_results = verify_fixes()
    
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
