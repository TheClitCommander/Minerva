"""
WebSocket Request Tracker for Minerva

Provides timeout monitoring and fallback responses for WebSocket requests
to ensure all requests eventually complete.
"""
import logging
import threading
import time
from datetime import datetime

# Setup logging
logger = logging.getLogger('websocket_tracker')

# Default timeout in seconds
DEFAULT_TIMEOUT = 30

class RequestTracker:
    """Tracks active WebSocket requests and handles timeouts"""
    
    def __init__(self, timeout_seconds=DEFAULT_TIMEOUT):
        self.active_requests = {}
        self.timeout_seconds = timeout_seconds
        self._lock = threading.Lock()
        logger.info(f"🕒 Initialized RequestTracker with {timeout_seconds}s timeout")
    
    def add_request(self, message_id, session_id, emit_func):
        """Register a new active request"""
        with self._lock:
            self.active_requests[message_id] = {
                'timestamp': datetime.now(),
                'session_id': session_id,
                'emit_func': emit_func,
                'completed': False
            }
        logger.info(f"➕ Added request {message_id} to tracking")
    
    def complete_request(self, message_id):
        """Mark a request as completed"""
        with self._lock:
            if message_id in self.active_requests:
                self.active_requests[message_id]['completed'] = True
                logger.info(f"✅ Marked request {message_id} as completed")
                return True
        return False
    
    def check_timeouts(self):
        """Check for requests that have timed out"""
        now = datetime.now()
        timed_out = []
        
        with self._lock:
            for message_id, request in list(self.active_requests.items()):
                if not request['completed']:
                    elapsed = (now - request['timestamp']).total_seconds()
                    if elapsed > self.timeout_seconds:
                        timed_out.append(message_id)
        
        # Handle timeouts
        for message_id in timed_out:
            self.handle_timeout(message_id)
        
        # Clean up completed requests
        self.cleanup_old_requests()
        
        return len(timed_out)
    
    def handle_timeout(self, message_id):
        """Handle a timed out request by sending fallback response"""
        with self._lock:
            if message_id not in self.active_requests:
                return
                
            request = self.active_requests[message_id]
            if request['completed']:
                return
                
            session_id = request['session_id']
            emit_func = request['emit_func']
        
        logger.warning(f"⏰ [TIMEOUT] Request {message_id} timed out after {self.timeout_seconds}s")
        
        try:
            # Send fallback response
            emit_func('response', {
                'message_id': message_id,
                'session_id': session_id,
                'response': "I'm sorry, but this request has timed out. Please try again.",
                'source': 'Timeout Fallback',
                'model_info': {'error': True, 'timeout': True}
            }, room=session_id)
            
            logger.info(f"📤 [FALLBACK_SENT] Sent timeout fallback for {message_id}")
            
            # Mark as completed
            self.complete_request(message_id)
            
        except Exception as e:
            logger.error(f"❌ [FALLBACK_ERROR] Failed to send timeout fallback: {str(e)}")
    
    def cleanup_old_requests(self, max_age_minutes=5):
        """Remove old completed requests"""
        now = datetime.now()
        to_remove = []
        
        with self._lock:
            for message_id, request in list(self.active_requests.items()):
                if request['completed']:
                    age = (now - request['timestamp']).total_seconds() / 60.0
                    if age > max_age_minutes:
                        to_remove.append(message_id)
            
            # Remove old requests
            for message_id in to_remove:
                del self.active_requests[message_id]
                
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old completed requests")
            
# Singleton instance
_request_tracker = None

def get_request_tracker():
    """Get the global request tracker instance"""
    global _request_tracker
    if _request_tracker is None:
        _request_tracker = RequestTracker()
        
        # Start the background monitor thread
        def monitor_timeouts():
            while True:
                try:
                    timeouts = _request_tracker.check_timeouts()
                    if timeouts > 0:
                        logger.info(f"⏰ Timeout monitor found {timeouts} timed out requests")
                except Exception as e:
                    logger.error(f"Error in timeout monitor: {str(e)}")
                time.sleep(5)  # Check every 5 seconds
                
        # Start monitor thread
        monitor_thread = threading.Thread(target=monitor_timeouts, daemon=True)
        monitor_thread.start()
        logger.info("🔄 Started request timeout monitor thread")
        
    return _request_tracker
