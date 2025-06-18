#!/usr/bin/env python
"""
Coordinator Verification Script

This script tests whether the AI Coordinator is properly initialized and accessible
from different import patterns. It helps diagnose import issues with the coordinator.
"""

import os
import sys
import importlib
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import_patterns():
    """Test different import patterns for the coordinator"""
    print("\n==== Testing Coordinator Import Patterns ====\n")
    
    results = {
        "direct_import_capital": False,
        "direct_import_lowercase": False,
        "module_import_capital": False,
        "module_import_lowercase": False,
        "module_import_uppercase": False,
        "singleton_instance": False,
        "create_new_instance": False,
    }
    
    # Test 1: Direct import with capital C
    print("\nTest 1: Direct import 'Coordinator' (capital C)")
    try:
        from web.multi_ai_coordinator import Coordinator
        if Coordinator is not None:
            has_generate = hasattr(Coordinator, 'generate_response') and callable(getattr(Coordinator, 'generate_response'))
            has_models = hasattr(Coordinator, 'available_models')
            
            results["direct_import_capital"] = True
            print(f"✅ Success: Imported Coordinator directly")
            print(f"  - Type: {type(Coordinator).__name__}")
            print(f"  - Has generate_response(): {has_generate}")
            print(f"  - Has available_models: {has_models}")
            
            if has_models:
                models = list(Coordinator.available_models.keys())
                print(f"  - Available models: {models}")
        else:
            print("❌ Failed: Coordinator is None")
    except (ImportError, AttributeError) as e:
        print(f"❌ Failed: {str(e)}")
    
    # Test 2: Direct import with lowercase c
    print("\nTest 2: Direct import 'coordinator' (lowercase c)")
    try:
        from web.multi_ai_coordinator import coordinator
        if coordinator is not None:
            has_generate = hasattr(coordinator, 'generate_response') and callable(getattr(coordinator, 'generate_response'))
            has_models = hasattr(coordinator, 'available_models')
            
            results["direct_import_lowercase"] = True
            print(f"✅ Success: Imported coordinator directly")
            print(f"  - Type: {type(coordinator).__name__}")
            print(f"  - Has generate_response(): {has_generate}")
            print(f"  - Has available_models: {has_models}")
            
            if has_models:
                models = list(coordinator.available_models.keys())
                print(f"  - Available models: {models}")
        else:
            print("❌ Failed: coordinator is None")
    except (ImportError, AttributeError) as e:
        print(f"❌ Failed: {str(e)}")
    
    # Test 3: Module import
    print("\nTest 3: Module import patterns")
    try:
        import web.multi_ai_coordinator as multi_ai_mod
        
        # Print available attributes
        print(f"Available module attributes: {[attr for attr in dir(multi_ai_mod) if not attr.startswith('__')]}")
        
        # Check for Coordinator (capital C)
        if hasattr(multi_ai_mod, 'Coordinator'):
            coord = multi_ai_mod.Coordinator
            if coord is not None:
                has_generate = hasattr(coord, 'generate_response') and callable(getattr(coord, 'generate_response'))
                has_models = hasattr(coord, 'available_models')
                
                results["module_import_capital"] = True
                print(f"✅ Success: Module contains Coordinator (capital C)")
                print(f"  - Type: {type(coord).__name__}")
                print(f"  - Has generate_response(): {has_generate}")
                print(f"  - Has available_models: {has_models}")
                
                if has_models:
                    models = list(coord.available_models.keys())
                    print(f"  - Available models: {models}")
            else:
                print("❌ Failed: multi_ai_mod.Coordinator is None")
        else:
            print("❌ Failed: Module does not have 'Coordinator' attribute")
        
        # Check for coordinator (lowercase c)
        if hasattr(multi_ai_mod, 'coordinator'):
            coord = multi_ai_mod.coordinator
            if coord is not None:
                has_generate = hasattr(coord, 'generate_response') and callable(getattr(coord, 'generate_response'))
                has_models = hasattr(coord, 'available_models')
                
                results["module_import_lowercase"] = True
                print(f"✅ Success: Module contains coordinator (lowercase c)")
                print(f"  - Type: {type(coord).__name__}")
                print(f"  - Has generate_response(): {has_generate}")
                print(f"  - Has available_models: {has_models}")
                
                if has_models:
                    models = list(coord.available_models.keys())
                    print(f"  - Available models: {models}")
            else:
                print("❌ Failed: multi_ai_mod.coordinator is None")
        else:
            print("❌ Failed: Module does not have 'coordinator' attribute")
        
        # Check for COORDINATOR (uppercase)
        if hasattr(multi_ai_mod, 'COORDINATOR'):
            coord = multi_ai_mod.COORDINATOR
            if coord is not None:
                has_generate = hasattr(coord, 'generate_response') and callable(getattr(coord, 'generate_response'))
                has_models = hasattr(coord, 'available_models')
                
                results["module_import_uppercase"] = True
                print(f"✅ Success: Module contains COORDINATOR (uppercase)")
                print(f"  - Type: {type(coord).__name__}")
                print(f"  - Has generate_response(): {has_generate}")
                print(f"  - Has available_models: {has_models}")
                
                if has_models:
                    models = list(coord.available_models.keys())
                    print(f"  - Available models: {models}")
            else:
                print("❌ Failed: multi_ai_mod.COORDINATOR is None")
        else:
            print("❌ Failed: Module does not have 'COORDINATOR' attribute")
        
        # Check for singleton instance
        if hasattr(multi_ai_mod, 'MultiAICoordinator'):
            if hasattr(multi_ai_mod.MultiAICoordinator, '_instance'):
                inst = multi_ai_mod.MultiAICoordinator._instance
                if inst is not None:
                    has_generate = hasattr(inst, 'generate_response') and callable(getattr(inst, 'generate_response'))
                    has_models = hasattr(inst, 'available_models')
                    
                    results["singleton_instance"] = True
                    print(f"✅ Success: MultiAICoordinator has _instance")
                    print(f"  - Type: {type(inst).__name__}")
                    print(f"  - Has generate_response(): {has_generate}")
                    print(f"  - Has available_models: {has_models}")
                    
                    if has_models:
                        models = list(inst.available_models.keys())
                        print(f"  - Available models: {models}")
                else:
                    print("❌ Failed: MultiAICoordinator._instance is None")
            else:
                print("❌ Failed: MultiAICoordinator does not have '_instance' attribute")
        else:
            print("❌ Failed: Module does not have 'MultiAICoordinator' attribute")
        
        # Try creating a new instance
        if hasattr(multi_ai_mod, 'MultiAICoordinator'):
            try:
                new_instance = multi_ai_mod.MultiAICoordinator()
                if new_instance is not None:
                    has_generate = hasattr(new_instance, 'generate_response') and callable(getattr(new_instance, 'generate_response'))
                    has_models = hasattr(new_instance, 'available_models')
                    
                    results["create_new_instance"] = True
                    print(f"✅ Success: Created new MultiAICoordinator instance")
                    print(f"  - Type: {type(new_instance).__name__}")
                    print(f"  - Has generate_response(): {has_generate}")
                    print(f"  - Has available_models: {has_models}")
                    
                    if has_models:
                        models = list(new_instance.available_models.keys())
                        print(f"  - Available models: {models}")
                else:
                    print("❌ Failed: Created instance is None")
            except Exception as e:
                print(f"❌ Failed to create instance: {str(e)}")
        
    except Exception as e:
        print(f"❌ Failed to import module: {str(e)}")
    
    # Summary
    print("\n==== Summary of Import Tests ====")
    for test, result in results.items():
        print(f"{'✅' if result else '❌'} {test.replace('_', ' ').title()}")
    
    success_count = sum(1 for r in results.values() if r)
    print(f"\nPassed {success_count} out of {len(results)} tests")
    
    # Final result
    if any(results.values()):
        print("\n✅ Success: Found at least one working import pattern!")
        return True
    else:
        print("\n❌ Critical Failure: No working import patterns found")
        return False

def test_minerva_extensions():
    """Test the MinervaExtensions with coordinator"""
    print("\n==== Testing MinervaExtensions Integration ====\n")
    
    try:
        from web.minerva_extensions import MinervaExtensions
        
        # First try with no explicit coordinator
        print("Test 1: Initialize MinervaExtensions without explicit coordinator")
        extensions = MinervaExtensions()
        
        # Check if it found a coordinator
        if extensions.coordinator:
            print(f"✅ Success: MinervaExtensions found a coordinator on its own")
            print(f"  - Coordinator type: {type(extensions.coordinator).__name__}")
            has_generate = hasattr(extensions.coordinator, 'generate_response') and callable(getattr(extensions.coordinator, 'generate_response'))
            print(f"  - Has generate_response(): {has_generate}")
            
            # Try to process a message
            try:
                response = extensions.process_message("Hello, test message")
                print(f"✅ Success: Generated response through MinervaExtensions")
                print(f"  - Response: {response.get('message', '')[:100]}...")
            except Exception as e:
                print(f"❌ Failed to process message: {str(e)}")
        else:
            print("❌ Failed: MinervaExtensions did not find a coordinator")
        
        # Now try with explicit coordinator
        print("\nTest 2: Initialize MinervaExtensions with explicit coordinator")
        try:
            # Get coordinator directly
            from web.multi_ai_coordinator import coordinator, Coordinator
            
            # Use whichever one is available
            coord = Coordinator if Coordinator is not None else coordinator
            
            if coord is not None:
                extensions2 = MinervaExtensions(coord)
                print(f"✅ Success: Created MinervaExtensions with explicit coordinator")
                print(f"  - Coordinator type: {type(extensions2.coordinator).__name__}")
                
                # Try to process a message
                try:
                    response = extensions2.process_message("Hello, test message with explicit coordinator")
                    print(f"✅ Success: Generated response through MinervaExtensions with explicit coordinator")
                    print(f"  - Response: {response.get('message', '')[:100]}...")
                except Exception as e:
                    print(f"❌ Failed to process message with explicit coordinator: {str(e)}")
            else:
                print("❌ Failed: No coordinator available to pass to MinervaExtensions")
        except (ImportError, AttributeError) as e:
            print(f"❌ Failed to import coordinator: {str(e)}")
        
    except ImportError as e:
        print(f"❌ Failed to import MinervaExtensions: {str(e)}")
    except Exception as e:
        print(f"❌ Failed to test MinervaExtensions: {str(e)}")
        traceback.print_exc()

def main():
    print("\n" + "="*50)
    print(" Minerva Coordinator Verification Tool ")
    print("="*50 + "\n")
    
    print("This tool checks if the MultiAICoordinator is properly initialized")
    print("and accessible from different import patterns\n")
    
    # Test import patterns
    coordinator_success = test_import_patterns()
    
    # Test MinervaExtensions
    test_minerva_extensions()
    
    print("\n" + "="*50)
    if coordinator_success:
        print("✅ CONCLUSION: Coordinator is properly initialized and accessible")
        print("   You should be able to get real AI responses now")
    else:
        print("❌ CONCLUSION: Coordinator initialization has issues")
        print("   Socket.IO chat will likely continue to use simulated responses")
    print("="*50 + "\n")

if __name__ == "__main__":
    main() 