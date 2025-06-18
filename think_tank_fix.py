"""
Enhanced Think Tank Processor for Minerva

Features:
- Parallel model processing with threading
- Timeout handling for slow models
- Detailed error logging and diagnostics
- Guaranteed fallback responses
"""
import time
import logging
import os
from threading import Thread
from datetime import datetime, timedelta
from flask_socketio import emit

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/think_tank_fix.log',
    filemode='a'
)
logger = logging.getLogger('think_tank_fix')

THINK_TANK_TIMEOUT = 25  # Max seconds to wait for AI responses
FALLBACK_RESPONSE = "I apologize, but I encountered an issue processing this request. Please try again later."

class ThinkTankProcessor:
    """Handles multi-model AI coordination in Think Tank Mode."""
    
    def __init__(self, models):
        self.models = models  # List of AI models (e.g., [Claude, GPT-4])
    
    def process_request(self, message_id, session_id, query):
        """Handles a Think Tank request by querying multiple AI models."""
        responses = []
        model_errors = {}
        start_time = datetime.now()
        
        logger.info(f"🧠 [THINK_TANK_START] Processing message {message_id} using Think Tank mode")
        
        # Launch models in parallel
        threads = []
        for model in self.models:
            thread = Thread(target=self._query_model, args=(model, query, responses, model_errors))
            thread.start()
            threads.append(thread)
        
        # Wait for all models or timeout
        for thread in threads:
            thread.join(timeout=THINK_TANK_TIMEOUT)
        
        if not responses:
            logger.warning(f"⚠️ [THINK_TANK_FAIL] No models responded within {THINK_TANK_TIMEOUT} seconds")
            self._send_fallback_response(session_id, message_id, model_errors)
            return
        
        # Select best response (for now, just take the first valid response)
        final_response = responses[0]['response'] if responses else FALLBACK_RESPONSE
        model_info = responses[0]['model_info'] if responses else {'error': True}
        
        logger.info(f"✅ [THINK_TANK_SUCCESS] Returning response for message {message_id}")
        emit('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': final_response,
            'source': 'Think Tank Mode',
            'model_info': model_info,
            'processing_time': (datetime.now() - start_time).total_seconds()
        }, room=session_id)
    
    def _query_model(self, model, query, responses, model_errors):
        """Queries an AI model and stores the result if successful."""
        try:
            start_time = time.time()
            response = model.generate_response(query)
            processing_time = time.time() - start_time
            
            if response:
                responses.append({
                    'response': response, 
                    'model': model.name, 
                    'model_info': {
                        'name': model.name, 
                        'processing_time': processing_time
                    }
                })
                logger.info(f"✅ [MODEL_SUCCESS] {model.name} returned a response in {processing_time:.2f}s")
            else:
                model_errors[model.name] = "Empty response"
                logger.warning(f"⚠️ [MODEL_EMPTY] {model.name} returned an empty response")
        except Exception as e:
            model_errors[model.name] = str(e)
            logger.error(f"❌ [MODEL_ERROR] {model.name} failed with error: {str(e)}")
    
    def _send_fallback_response(self, session_id, message_id, errors=None):
        """Sends a fallback response if Think Tank mode fails."""
        try:
            emit('response', {
                'message_id': message_id,
                'session_id': session_id,
                'response': FALLBACK_RESPONSE,
                'source': 'Think Tank Fallback',
                'model_info': {'error': True, 'model_errors': errors or {}, 'fallback': True}
            }, room=session_id)
            logger.info(f"📤 [FALLBACK_SENT] Sent fallback for message {message_id}")
        except Exception as e:
            logger.error(f"❌ [FALLBACK_ERROR] Failed to send fallback response: {str(e)}")
