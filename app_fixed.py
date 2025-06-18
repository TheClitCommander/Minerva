def process_message_thread():
    # Initialize response to track if we're getting a response at all
    response = None
    processing_method = "unknown"
    model_info = {}
    
    try:
        # Let the user know we're processing their message
        emit('processing_update', {
            'session_id': session_id,
            'message_id': message_id,
            'status': 'processing',
            'step': 'Starting message processing'
        })
        
        # Check if framework is available by trying to access it
        framework_available = False
        try:
            from integrations.framework_manager import framework_manager
            
            # Actively try to load the HuggingFace framework
            framework_manager.ensure_huggingface_loaded()
            emit('processing_update', {'step': 'Checked framework availability'})
            
            # Now check if it's loaded
            huggingface = framework_manager.get_framework_by_name("HuggingFace")
            if huggingface:
                framework_available = True
                logger.info("Successfully loaded HuggingFace framework")
                print("[WEBSOCKET DEBUG] HuggingFace framework is available")
        except Exception as e:
            logger.warning(f"Could not access HuggingFace framework: {str(e)}")
            framework_available = False
            print(f"[WEBSOCKET DEBUG] HuggingFace framework not available: {str(e)}")

        # Check if Think Tank mode is requested
        # First, log the raw data for debugging
        logger.info(f"[WEBSOCKET DEBUG] Raw message data: {data}")
        
        # Extract mode parameter with fallbacks for different structures
        mode = data.get('mode', '')
        
        # Check for mode in various nested structures
        if not mode and isinstance(data, dict):
            # Check if mode is in a parameters or options subfield
            if 'parameters' in data and isinstance(data['parameters'], dict):
                mode = data['parameters'].get('mode', '')
            elif 'options' in data and isinstance(data['options'], dict):
                mode = data['options'].get('mode', '')
            elif 'data' in data and isinstance(data['data'], dict):
                mode = data['data'].get('mode', '')
        
        logger.info(f"[WEBSOCKET DEBUG] Extracted mode: '{mode}'")
        
        # Extract other parameters
        test_mode = data.get('test_mode', False)
        include_model_info = data.get('include_model_info', False)
        
        emit('processing_update', {'step': f'Processing with mode: {mode}', 'mode_found': bool(mode)})
        
        # Process based on mode and available models
        try:
            # Use Think Tank mode if requested
            if mode == 'think_tank':
                logger.info(f"[WEBSOCKET] Think Tank mode requested")
                try:
                    # Add more detailed logging for the import process
                    logger.info(f"[WEBSOCKET DEBUG] Attempting to import MultiAICoordinator...")
                    try:
                        from web.multi_ai_coordinator import MultiAICoordinator
                        logger.info(f"[WEBSOCKET DEBUG] Successfully imported MultiAICoordinator from web.multi_ai_coordinator")
                    except ImportError:
                        logger.info(f"[WEBSOCKET DEBUG] Import from web.multi_ai_coordinator failed, trying direct import...")
                        from multi_ai_coordinator import MultiAICoordinator
                        logger.info(f"[WEBSOCKET DEBUG] Successfully imported MultiAICoordinator from direct import")
                    
                    # Get coordinator instance with enhanced logging
                    logger.info(f"[WEBSOCKET DEBUG] Getting MultiAICoordinator instance...")
                    coordinator = MultiAICoordinator.get_instance()
                    logger.info(f"[WEBSOCKET DEBUG] Coordinator instance type: {type(coordinator).__name__}")
                    logger.info(f"[WEBSOCKET DEBUG] Coordinator instance ID: {id(coordinator)}")
                    
                    # Check for registered models
                    if hasattr(coordinator, 'model_registry') and coordinator.model_registry:
                        model_count = len(coordinator.model_registry.get_available_models())
                        logger.info(f"[WEBSOCKET DEBUG] Coordinator has {model_count} registered models")
                    else:
                        logger.error(f"[WEBSOCKET DEBUG] Coordinator has NO model registry or NO registered models")
                    
                    if coordinator:
                        logger.info(f"[WEBSOCKET] Coordinator instance found")
                        emit('processing_update', {'step': 'Using Think Tank mode'})
                        processing_method = "think_tank"
                        
                        # Create headers dict with test mode if specified
                        headers = {}
                        if test_mode:
                            headers['X-Test-Mode'] = 'true'
                            logger.info(f"[WEBSOCKET] Added X-Test-Mode header")
                    
                    # Process with Think Tank - handle async properly
                    logger.info(f"[WEBSOCKET] Calling coordinator.process_message with mode: think_tank, test_mode: {test_mode}")
                    
                    # Check if coordinator exists and has expected methods
                    logger.info(f"[WEBSOCKET] Coordinator type: {type(coordinator).__name__}")
                    logger.info(f"[WEBSOCKET] Coordinator has process_message: {hasattr(coordinator, 'process_message')}")
                    
                    if hasattr(coordinator, 'process_message'):
                        process_message_func = coordinator.process_message
                        logger.info(f"[WEBSOCKET] process_message type: {type(process_message_func).__name__}")
                        
                        # Handle the async nature of process_message
                        try:
                            import asyncio
                            # Check if the method is actually async
                            if asyncio.iscoroutinefunction(coordinator.process_message):
                                logger.info(f"[WEBSOCKET] Detected async process_message, using asyncio")
                                # Create a new event loop for this thread if needed
                                try:
                                    loop = asyncio.get_event_loop()
                                except RuntimeError:
                                    logger.info(f"[WEBSOCKET] Creating new event loop")
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                
                                # Run the async function and get the result
                                logger.info(f"[WEBSOCKET] About to call process_message with: {message[:100]}...")
                                # Explicit parameter order to ensure consistency
                                try:
                                    # CRITICAL FIX: Properly await the async call with timeout
                                    result = loop.run_until_complete(
                                        asyncio.wait_for(
                                            coordinator.process_message(
                                                message=message, 
                                                user_id=user_id,
                                                message_id=message_id, 
                                                mode='think_tank',
                                                include_model_info=include_model_info,
                                                test_mode=test_mode,
                                                headers=headers
                                            ),
                                            timeout=30.0  # Add timeout to prevent hanging
                                        )
                                    )
                                    logger.info(f"[WEBSOCKET] async process_message call completed successfully")
                                except asyncio.TimeoutError:
                                    logger.error(f"[WEBSOCKET] Timeout error in async process_message after 30 seconds")
                                    raise Exception("Request timed out. The models are taking too long to respond.")
                                except Exception as e:
                                    logger.error(f"[WEBSOCKET] Error in async process_message: {str(e)}", exc_info=True)
                                    raise
                                logger.info(f"[WEBSOCKET] Think Tank Response received with type: {type(result).__name__}")
                                if result:
                                    logger.info(f"[WEBSOCKET] Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                            else:
                                # Call directly if it's not async
                                logger.info(f"[WEBSOCKET] Using synchronous process_message")
                                result = coordinator.process_message(
                                    message=message, 
                                    user_id=user_id,
                                    message_id=message_id,
                                    mode='think_tank',
                                    include_model_info=include_model_info,
                                    test_mode=test_mode,
                                    headers=headers
                                )
                            
                            # Log detailed info about the result
                            if result is None:
                                logger.error(f"[WEBSOCKET] Coordinator returned None instead of a valid result")
                                raise Exception("Coordinator returned None result")
                                
                            if not isinstance(result, dict):
                                logger.error(f"[WEBSOCKET] Coordinator returned {type(result).__name__} instead of dict")
                                raise Exception(f"Coordinator returned {type(result).__name__} instead of dict")
                                
                            logger.info(f"[WEBSOCKET] Coordinator result keys: {list(result.keys())}")
                            response = result.get('response', '')
                            if not response:
                                logger.error(f"[WEBSOCKET] Response is empty or missing in result: {result}")
                                
                            model_info = result.get('model_info', {})
                            logger.info(f"[WEBSOCKET] Model info is present: {model_info is not None}")
                            
                            # Detailed logging of response and model_info
                            if response:
                                print(f"[WEBSOCKET DEBUG] Response type: {type(response).__name__}, length: {len(response)}")
                            else:
                                print(f"[WEBSOCKET DEBUG] Response is empty or None: {response}")
                                
                            if model_info:
                                print(f"[WEBSOCKET DEBUG] model_info keys: {list(model_info.keys())}")
                                if 'models_used' in model_info:
                                    print(f"[WEBSOCKET DEBUG] Models used: {model_info['models_used']}")
                            else:
                                print(f"[WEBSOCKET DEBUG] model_info is empty or None: {model_info}")
                                
                            emit('processing_update', {'step': 'Think Tank processing complete'})
                            
                        except Exception as e:
                            logger.error(f"[WEBSOCKET] Error processing with Think Tank: {str(e)}", exc_info=True)
                            # Fallback to empty response
                            response = f"Error processing your message: {str(e)}"
                            model_info = {"error": str(e)}
                            logger.info(f"[WEBSOCKET] Got error response from Think Tank: {response[:50]}... with error: {str(e)}")
                            print(f"[WEBSOCKET DEBUG] Got error response from Think Tank: {response[:50]}...")
                    else:
                        # Fallback if coordinator not available
                        emit('processing_update', {'step': 'Think Tank not available, using fallback'})
                        raise Exception("MultiAICoordinator not available")
                except Exception as e:
                    logger.error(f"Error using Think Tank mode: {str(e)}")
                    # Fall through to regular processing
                    emit('processing_update', {'step': 'Falling back to standard processing'})
            
            # Regular processing if not Think Tank or if Think Tank failed
            if 'response' not in locals() or not response:
                # Code for regular processing would go here
                logger.info("Regular processing placeholder")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            response = f"Error: {str(e)}"
            
    except Exception as e:
        logger.error(f"Error in message thread: {str(e)}")
        try:
            # Fallback response
            emit('response', {
                'session_id': session_id,
                'message_id': message_id,
                'response': f"Error processing your message: {str(e)}",
                'error': str(e)
            })
        except Exception as e2:
            # Last resort error
            emit('error', {
                'code': 'processing_error',
                'message': f"Error processing your message: {str(e2)}"
            })
