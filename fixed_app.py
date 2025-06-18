# We'll only include a minimal version of the function to fix the syntax error
def process_message_thread():
    try:
        # Main try block
        if mode == 'think_tank':
            try:
                # Import coordinator
                from multi_ai_coordinator import MultiAICoordinator
                coordinator = MultiAICoordinator.get_instance()
                
                if hasattr(coordinator, 'process_message'):
                    try:
                        # Process message
                        result = coordinator.process_message(message)
                        print("Success")
                    except Exception as e:
                        print(f"Error processing: {e}")
                else:
                    # Coordinator doesn't have process_message
                    print("Coordinator missing process_message method")
                    raise Exception("MultiAICoordinator not available")
            except Exception as e:
                print(f"Error in think tank mode: {e}")
                # Fall through to standard processing
    except Exception as e:
        print(f"Error in main try block: {e}")
