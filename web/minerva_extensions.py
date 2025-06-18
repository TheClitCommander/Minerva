"""
Minerva Extensions

This module extends the functionality of the Minerva Chat interface
with web research capabilities, persistent chat history, and
better model selection. It builds upon the existing Think Tank functionality.
"""

import os
import sys
import json
import time
import logging
import requests
import uuid
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)
file_handler = logging.FileHandler('logs/minerva_extensions.log')
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

class ChatHistory:
    """Class for managing chat history."""
    
    def __init__(self, storage_dir="data/chat_history"):
        """Initialize the chat history manager."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        logger.info(f"ChatHistory initialized with storage at {storage_dir}")
        
    def create_session(self, user_id="anonymous"):
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": time.time(),
            "messages": []
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        return session_id
        
    def session_exists(self, session_id):
        """Check if a session exists."""
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        return os.path.exists(session_file)
        
    def add_message(self, session_id, role, content, metadata=None):
        """Add a message to a chat session."""
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            logger.warning(f"Session {session_id} does not exist")
            return None
            
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            message_id = str(uuid.uuid4())
            message = {
                "id": message_id,
                "role": role,
                "content": content,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            session_data["messages"].append(message)
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            return message_id
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {str(e)}")
            return None
    
    def get_session_messages(self, session_id, limit=None, include_metadata=False):
        """Get messages from a chat session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return
            include_metadata: Whether to include metadata in returned messages
            
        Returns:
            List of message dictionaries or None if session not found
        """
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            logger.warning(f"Session {session_id} does not exist")
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            messages = session_data["messages"]
            
            # Apply limit if specified
            if limit is not None:
                messages = messages[-limit:]
            
            # Remove metadata if not requested
            if not include_metadata:
                messages = [{k: v for k, v in msg.items() if k != 'metadata'} 
                            for msg in messages]
            
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from session {session_id}: {str(e)}")
            return None
    
    def get_all_sessions(self, user_id=None):
        """Get summary information about all sessions.
        
        Args:
            user_id: Optional filter to only include sessions for this user
            
        Returns:
            List of session summary dictionaries
        """
        sessions = []
        for session_file in Path(self.storage_dir).glob("*.json"):
            session_id = session_file.stem
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Filter by user_id if specified
            if user_id and session_data["user_id"] != user_id:
                continue
            
            # Create summary
            sessions.append({
                "session_id": session_id,
                "user_id": session_data["user_id"],
                "created_at": session_data["created_at"],
                "updated_at": session_data["updated_at"],
                "message_count": len(session_data["messages"])
            })
        
        return sessions
    
    def delete_session(self, session_id):
        """Delete a chat session by ID"""
        try:
            if not os.path.exists(os.path.join(self.storage_dir, f"{session_id}.json")):
                logger.warning(f"Session {session_id} not found for deletion")
                return False
            
            # Delete the session file
            os.remove(os.path.join(self.storage_dir, f"{session_id}.json"))
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def create_test_session(self):
        """Create a test session for health checks
        
        Returns:
            str: The session ID if successful, None otherwise
        """
        try:
            # Create a temporary session ID with test prefix
            session_id = f"test_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Create an empty session with minimal data
            session_data = {
                "messages": [],
                "created_at": time.time(),
                "updated_at": time.time(),
                "metadata": {
                    "type": "test_session",
                    "purpose": "health_check"
                }
            }
            
            # Write session to file
            with open(os.path.join(self.storage_dir, f"{session_id}.json"), 'w') as f:
                json.dump(session_data, f)
                
            logger.debug(f"Created test session {session_id} for health check")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating test session: {str(e)}")
            return None
    
    def close(self):
        """Close any open resources"""
        # Currently we just use file-based storage, but this method
        # could close database connections or other resources in the future
        logger.info("Closing ChatHistory resources")
        return True
        
    def cleanup_old_sessions(self, ttl=None):
        """Remove sessions older than TTL.
        
        Args:
            ttl: Time-to-live in seconds (default: self.message_ttl)
        
        Returns:
            int: Number of sessions removed
        """
        ttl = ttl or 30 * 24 * 60 * 60  # 30 days in seconds
        now = datetime.now()
        removed_count = 0
        
        try:
            for session_file in Path(self.storage_dir).glob("*.json"):
                try:
                    session_id = session_file.stem
                    
                    # Skip test sessions as they should be removed separately
                    if session_id.startswith("test_"):
                        continue
                        
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    updated_at = datetime.fromtimestamp(session_data.get("updated_at", 0))
                    age_seconds = (now - updated_at).total_seconds()
                    
                    if age_seconds > ttl:
                        if self.delete_session(session_id):
                            removed_count += 1
                except Exception as e:
                    logger.error(f"Error processing session file {session_file}: {str(e)}")
            
            logger.info(f"Cleaned up {removed_count} old chat sessions")
            return removed_count
        except Exception as e:
            logger.error(f"Error in cleanup_old_sessions: {str(e)}")
            return 0


class WebResearcher:
    """Provides web research capabilities for AI responses."""
    
    def __init__(self, api_key=None, search_provider="duckduckgo"):
        """Initialize web researcher.
        
        Args:
            api_key: Optional API key for search provider
            search_provider: Search provider to use
        """
        self.api_key = api_key
        self.search_provider = search_provider
        self.cache_dir = Path('data/web_research_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 60 * 60  # 1 hour in seconds
        
        logger.info(f"WebResearcher initialized with {search_provider} provider")
    
    def search(self, query, max_results=5, depth="medium"):
        """Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            depth: Research depth (light, medium, deep)
            
        Returns:
            List of search result dictionaries
        """
        # Check cache first
        cache_key = f"{query}_{max_results}_{depth}"
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            logger.info(f"Using cached results for '{query}'")
            return cached_results
        
        # Convert depth to number of results
        result_counts = {
            "light": 3,
            "medium": 5,
            "deep": 10
        }
        count = result_counts.get(depth, 5)
        
        logger.info(f"Searching web for '{query}' with depth {depth}")
        
        # Perform search based on provider
        results = []
        
        if self.search_provider == "duckduckgo":
            results = self._search_duckduckgo(query, count)
        elif self.search_provider == "google":
            results = self._search_with_api("google", query, count)
        elif self.search_provider == "bing":
            results = self._search_with_api("bing", query, count)
        else:
            logger.warning(f"Unsupported search provider: {self.search_provider}")
            results = []
        
        # Cache results
        self._save_to_cache(cache_key, results)
        
        return results[:max_results]
    
    def fetch_content(self, url):
        """Fetch content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with 'content' and 'metadata' keys
        """
        # Check cache first
        cache_key = f"content_{url}"
        cached_content = self._get_from_cache(cache_key)
        if cached_content:
            logger.info(f"Using cached content for {url}")
            return cached_content
        
        logger.info(f"Fetching content from {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract content (simplified version)
            content = response.text
            
            # Add metadata
            result = {
                "content": content,
                "metadata": {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get('Content-Type', ''),
                    "fetched_at": datetime.now().isoformat()
                }
            }
            
            # Cache results
            self._save_to_cache(cache_key, result)
            
            return result
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return {
                "content": "",
                "metadata": {
                    "url": url,
                    "error": str(e),
                    "fetched_at": datetime.now().isoformat()
                }
            }
    
    def research(self, query, max_sources=3, depth="medium"):
        """Perform complete research on a query.
        
        Args:
            query: Research query
            max_sources: Maximum number of sources to use
            depth: Research depth (light, medium, deep)
            
        Returns:
            Dictionary with 'summary', 'sources', and 'search_results' keys
        """
        # Perform search
        search_results = self.search(query, max_results=max_sources, depth=depth)
        
        # Fetch content from top results
        sources = []
        for result in search_results[:max_sources]:
            content = self.fetch_content(result["url"])
            if content and content.get("content"):
                sources.append({
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"],
                    "content": content["content"][:5000]  # Limit content size
                })
        
        # Return all research data
        research_data = {
            "query": query,
            "sources": sources,
            "search_results": search_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed research on '{query}' with {len(sources)} sources")
        return research_data
    
    def _search_duckduckgo(self, query, count=5):
        """Search using DuckDuckGo (simulated for now).
        
        In a production system, you would use the actual DuckDuckGo API or web scraping.
        """
        # Simulate DuckDuckGo search results
        results = [
            {
                "title": f"Simulated Result {i} for '{query}'",
                "url": f"https://example.com/result{i}",
                "snippet": f"This is a snippet for search result {i} related to {query}..."
            }
            for i in range(1, count + 1)
        ]
        
        return results
    
    def _search_with_api(self, provider, query, count=5):
        """Search using an API-based provider.
        
        Args:
            provider: API provider (google, bing)
            query: Search query
            count: Number of results
            
        Returns:
            List of search result dictionaries
        """
        # In a real implementation, you would make API calls to the search provider
        # For now, we'll simulate results
        results = [
            {
                "title": f"{provider.capitalize()} Result {i} for '{query}'",
                "url": f"https://example.com/{provider}/result{i}",
                "snippet": f"This is a snippet from {provider} for search result {i} related to {query}..."
            }
            for i in range(1, count + 1)
        ]
        
        return results
    
    def _get_cache_path(self, key):
        """Get filesystem path for a cache key."""
        # Create a filename-safe version of the key
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"
    
    def _get_from_cache(self, key):
        """Get data from cache if available and not expired."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached_data["cached_at"])
            age_seconds = (datetime.now() - cached_time).total_seconds()
            
            if age_seconds > self.cache_ttl:
                logger.info(f"Cache expired for {key}")
                return None
            
            return cached_data["data"]
        except Exception as e:
            logger.error(f"Error reading cache for {key}: {str(e)}")
            return None
    
    def _save_to_cache(self, key, data):
        """Save data to cache."""
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    "data": data,
                    "cached_at": datetime.now().isoformat()
                }, f)
            return True
        except Exception as e:
            logger.error(f"Error saving cache for {key}: {str(e)}")
            return False


class MinervaExtensions:
    """Main class for Minerva extensions."""
    
    def __init__(self, coordinator=None):
        """
        Initialize the MinervaExtensions with optional AI coordinator.
        
        Args:
            coordinator: Optional AI coordinator instance
        """
        # Set up the coordinator
        self.coordinator = coordinator
        
        # If no coordinator provided, try to import it from singleton
        if self.coordinator is None:
            print("MinervaExtensions: No coordinator provided, attempting to import")
            
            try:
                # First try to import from the singleton file
                from ai_coordinator_singleton import coordinator, Coordinator
                self.coordinator = coordinator
                print(f"✅ MinervaExtensions: Successfully imported coordinator from singleton: {id(self.coordinator)}")
            except (ImportError, AttributeError) as e:
                print(f"MinervaExtensions: Error importing from singleton: {e}")
                
                # Fallback to direct import as a last resort
                try:
                    from web.multi_ai_coordinator import Coordinator
                    self.coordinator = Coordinator
                    print(f"MinervaExtensions: Using Coordinator from direct import: {id(self.coordinator)}")
                except (ImportError, AttributeError) as e:
                    print(f"❌ MinervaExtensions: Error importing coordinator: {e}")
                    self.coordinator = None
        
        # Set up the chat history manager
        self.chat_history = ChatHistory()
        logger.info("ChatHistory initialized with storage at data/chat_history")
        
        # Set up the web research client
        self.web_researcher = WebResearcher()
        logger.info("WebResearcher initialized with duckduckgo provider")
        
        self.active_sessions = {}
        
        # Final check to confirm coordinator status
        if self.coordinator:
            try:
                # Verify the coordinator has the required methods
                if hasattr(self.coordinator, 'generate_response') and callable(getattr(self.coordinator, 'generate_response')):
                    print(f"✅ MinervaExtensions: Successfully connected to coordinator")
                    logger.info(f"MinervaExtensions initialized with coordinator")
                else:
                    logger.warning("MinervaExtensions: Coordinator missing required methods")
                    self.coordinator = None
            except Exception as e:
                logger.error(f"Error verifying coordinator: {e}")
                self.coordinator = None
        
        if not self.coordinator:
            logger.warning("MultiAICoordinator not available, using simulated responses")
            print("WARNING: MultiAICoordinator not available, using simulated responses")
    
    def process_message(self, message, session_id=None, user_id=None, model_preference=None, enable_web_research=False, research_depth="medium"):
        """
        Process a message and generate a response.
        
        Args:
            message: The user message
            session_id: Optional session ID
            user_id: Optional user ID
            model_preference: Optional model preference
            enable_web_research: Whether to perform web research
            research_depth: Web research depth
            
        Returns:
            dict: Response with message content
        """
        print(f"[MinervaExtensions] Processing: {message[:100]} in session {session_id} with model {model_preference}")
        
        # Track timing for performance debugging
        start_time = time.time()
        
        try:
            # Generate message ID
            message_id = str(uuid.uuid4())
            
            # Save the message to chat history if session exists
            if session_id:
                if not self.chat_history.session_exists(session_id):
                    logger.info(f"Creating new session {session_id} for user {user_id or 'anonymous'}")
                    self.chat_history.create_session(user_id or "anonymous")
                    
                # Save the user message
                self.chat_history.add_message(session_id, "user", message)
            
            # Perform web research if enabled
            research_data = None
            if enable_web_research and self.web_researcher:
                try:
                    logger.info(f"Performing web research for: '{message}' with depth {research_depth}")
                    research_data = self.web_researcher.research(message, max_sources=3, depth=research_depth)
                    logger.info(f"Research complete with {len(research_data.get('sources', []))} sources")
                except Exception as e:
                    logger.error(f"Error performing web research: {str(e)}")
                    # Continue without research data
            
            # Augment the message with research data if available
            augmented_message = message
            if research_data and research_data.get('sources'):
                sources_text = "\n\nReference information:\n"
                for i, source in enumerate(research_data.get('sources', [])[:3], 1):
                    sources_text += f"{i}. {source.get('title', 'Untitled')}: {source.get('snippet', 'No snippet available')}\n"
                augmented_message = f"{message}\n\n{sources_text}"
            
            # Process with coordinator if available
            if self.coordinator:
                try:
                    logger.info(f"Using coordinator to generate response with model: {model_preference or 'default'}")
                    print(f"[MinervaExtensions] Using coordinator with model: {model_preference or 'default'}")
                    
                    # Generate response using the coordinator with the augmented message
                    ai_response = self.coordinator.generate_response(
                        augmented_message, 
                        session_id=session_id, 
                        model_preference=model_preference
                    )
                    
                    print(f"[MinervaExtensions] Coordinator returned response: {ai_response[:100]}...")
                    
                    # Get info about which model was used
                    available_models = self.coordinator.get_available_models()
                    used_model = model_preference if model_preference in available_models['models'] else available_models.get('default')
                    
                    # Create response object
                    response = {
                        "message": ai_response,
                        "message_id": message_id,
                        "session_id": session_id,
                        "model": used_model,
                        "model_info": {
                            "processing_time": f"{time.time() - start_time:.2f}s",
                            "web_research": bool(research_data)
                        }
                    }
                    
                    # Include research data if available
                    if research_data and research_data.get('sources'):
                        response["model_info"]["research_sources"] = [
                            {"title": source["title"], "url": source["url"]} 
                            for source in research_data["sources"]
                        ]
                    
                    # Save the AI response to chat history if session exists
                    if session_id:
                        metadata = {
                            "model": used_model,
                            "processing_time": f"{time.time() - start_time:.2f}s",
                            "web_research": bool(research_data)
                        }
                        self.chat_history.add_message(session_id, "ai", ai_response, metadata)
                    
                    logger.info(f"Generated AI response in {time.time() - start_time:.2f}s using model {used_model}")
                    print(f"[MinervaExtensions] Completed in {time.time() - start_time:.2f}s. Returning response.")
                    return response
                    
                except Exception as e:
                    logger.error(f"Error using coordinator: {str(e)}")
                    # Log stack trace for debugging
                    import traceback
                    logger.error(f"Stack trace: {traceback.format_exc()}")
                    print(f"[MinervaExtensions] ERROR when using coordinator: {str(e)}")
                    traceback.print_exc()
                    
                    # Fall through to error response, not simulation
                    error_message = f"I apologize, but I encountered an error while processing your message: {str(e)}"
                    return {
                        "message": error_message,
                        "message_id": message_id,
                        "session_id": session_id,
                        "model": "error",
                        "model_info": {
                            "error": str(e),
                            "processing_time": f"{time.time() - start_time:.2f}s"
                        }
                    }
            
            # If no coordinator available, return error message
            logger.warning("No AI coordinator available - cannot process message")
            print("[MinervaExtensions] WARNING: No AI coordinator available - using simulated response")
            
            # Generate a simulated response as fallback
            simulated = self.generate_simulated_response(message)
            print(f"[MinervaExtensions] Generated simulated response: {simulated[:100]}...")
            
            return {
                "message": simulated,
                "message_id": message_id,
                "session_id": session_id,
                "model": "simulated",
                "model_info": {
                    "processing_time": f"{time.time() - start_time:.2f}s",
                    "simulation": True
                }
            }
            
        except Exception as e:
            print(f"[MinervaExtensions ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            # Fall back to simulated response
            try:
                fallback_response = self.generate_simulated_response(message)
                print(f"[MinervaExtensions] Generated fallback response: {fallback_response[:100]}")
                
                return {
                    "message": fallback_response,
                    "message_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "model": "fallback",
                    "model_info": {
                        "error": str(e),
                        "processing_time": f"{time.time() - start_time:.2f}s",
                        "simulation": True
                    }
                }
                
            except Exception as inner_e:
                print(f"[MinervaExtensions CRITICAL ERROR] Even fallback failed: {str(inner_e)}")
                traceback.print_exc()
                return {
                    "message": f"I'm sorry, I couldn't process your message due to an error: {str(e)}",
                    "message_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "model": "error",
                    "model_info": {
                        "critical_error": True,
                        "processing_time": f"{time.time() - start_time:.2f}s"
                    }
                }
    
    def get_chat_history(self, session_id, limit=None):
        """Get chat history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of message dictionaries
        """
        return self.chat_history.get_session_messages(session_id, limit)
    
    def get_active_sessions(self, user_id=None):
        """Get active chat sessions.
        
        Args:
            user_id: Optional user identifier to filter by
            
        Returns:
            List of session dictionaries
        """
        return self.chat_history.get_all_sessions(user_id)
    
    def _simulate_ai_response(self, message, model_preference=None, research_data=None):
        """Simulate an AI response when the coordinator is not available.
        
        Args:
            message: User message
            model_preference: Optional model preference
            research_data: Optional web research data
            
        Returns:
            Dictionary with simulated response
        """
        model_used = model_preference or "blend"
        
        # Create base response
        response_text = f"This is a simulated response from {model_used} to: '{message}'"
        
        # Add research info if available
        if research_data:
            sources = [s["title"] for s in research_data.get("sources", [])]
            response_text += f"\n\nBased on web research from: {', '.join(sources)}"
        
        # Create response object
        response = {
            "message": response_text,
            "model_info": {
                "selected_mode": model_preference or "blend",
                "models_used": [f"Simulated {model_used.upper()}"],
                "top_model": f"Simulated {model_used.upper()}",
            }
        }
        
        # Add blending info for blend mode
        if not model_preference or model_preference == "blend":
            response["model_info"]["blending_strategy"] = "general_response_blending"
            response["model_info"]["query_type"] = "general"
            response["model_info"]["contributions"] = [
                {"model": "Simulated GPT-4", "weight": 0.6, "sections": ["intro", "technical details"]},
                {"model": "Simulated Claude-3", "weight": 0.3, "sections": ["examples", "conclusion"]},
                {"model": "Simulated Gemini", "weight": 0.1, "sections": ["comparisons"]}
            ]
        
        # Add research sources if available
        if research_data and "sources" in research_data:
            response["model_info"]["research_sources"] = [
                {"title": source["title"], "url": source["url"]} 
                for source in research_data["sources"]
            ]
        
        return response

    def generate_simulated_response(self, message):
        """Generate a simulated response for testing without real AI"""
        print(f"[MinervaExtensions] Generating simulated response for: {message[:100]}")


# Create singleton instance
minerva_extensions = MinervaExtensions()

