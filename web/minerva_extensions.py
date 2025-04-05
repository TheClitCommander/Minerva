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
    """Manages persistent chat history."""
    
    def __init__(self, storage_dir='data/chat_history'):
        """Initialize chat history manager.
        
        Args:
            storage_dir: Directory to store chat history files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.active_sessions = {}
        self.message_ttl = 30 * 24 * 60 * 60  # 30 days in seconds
        
        logger.info(f"ChatHistory initialized with storage at {self.storage_dir}")
    
    def get_session_path(self, session_id):
        """Get the filesystem path for a session."""
        return self.storage_dir / f"{session_id}.json"
    
    def create_session(self, user_id=None, metadata=None):
        """Create a new chat session.
        
        Args:
            user_id: Optional user identifier
            metadata: Optional metadata about the session
            
        Returns:
            session_id: Unique identifier for the created session
        """
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "created_at": timestamp,
            "updated_at": timestamp,
            "metadata": metadata or {},
            "messages": []
        }
        
        self.active_sessions[session_id] = session_data
        self._save_session(session_id)
        
        logger.info(f"Created new chat session {session_id} for user {user_id or 'anonymous'}")
        return session_id
    
    def add_message(self, session_id, message, sender_type, metadata=None):
        """Add a message to a chat session.
        
        Args:
            session_id: Session identifier
            message: The message text
            sender_type: 'user' or 'ai'
            metadata: Optional metadata about the message
            
        Returns:
            message_id: Unique identifier for the added message
        """
        # Load session if not in active sessions
        if session_id not in self.active_sessions:
            self._load_session(session_id)
        
        timestamp = datetime.now().isoformat()
        message_id = str(uuid.uuid4())
        
        message_data = {
            "id": message_id,
            "timestamp": timestamp,
            "sender_type": sender_type,
            "content": message,
            "metadata": metadata or {}
        }
        
        # Add message and update session
        self.active_sessions[session_id]["messages"].append(message_data)
        self.active_sessions[session_id]["updated_at"] = timestamp
        self._save_session(session_id)
        
        logger.info(f"Added {sender_type} message to session {session_id}")
        return message_id
    
    def get_session_messages(self, session_id, limit=None, include_metadata=False):
        """Get messages from a chat session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return
            include_metadata: Whether to include metadata in returned messages
            
        Returns:
            List of message dictionaries or None if session not found
        """
        # Load session if not in active sessions
        if session_id not in self.active_sessions:
            success = self._load_session(session_id)
            if not success:
                logger.warning(f"Session {session_id} not found")
                return None
        
        messages = self.active_sessions[session_id]["messages"]
        
        # Apply limit if specified
        if limit is not None:
            messages = messages[-limit:]
        
        # Remove metadata if not requested
        if not include_metadata:
            messages = [{k: v for k, v in msg.items() if k != 'metadata'} 
                        for msg in messages]
        
        return messages
    
    def get_all_sessions(self, user_id=None):
        """Get summary information about all sessions.
        
        Args:
            user_id: Optional filter to only include sessions for this user
            
        Returns:
            List of session summary dictionaries
        """
        # Load all sessions from disk
        self._load_all_sessions()
        
        sessions = []
        for session_id, session_data in self.active_sessions.items():
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
        """Delete a chat session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was deleted, False otherwise
        """
        session_path = self.get_session_path(session_id)
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Remove file if it exists
        if session_path.exists():
            session_path.unlink()
            logger.info(f"Deleted chat session {session_id}")
            return True
        
        logger.warning(f"Session {session_id} not found for deletion")
        return False
    
    def _save_session(self, session_id):
        """Save a session to disk."""
        if session_id not in self.active_sessions:
            logger.warning(f"Cannot save non-existent session {session_id}")
            return False
        
        session_path = self.get_session_path(session_id)
        
        with open(session_path, 'w') as f:
            json.dump(self.active_sessions[session_id], f)
        
        return True
    
    def _load_session(self, session_id):
        """Load a session from disk."""
        session_path = self.get_session_path(session_id)
        
        if not session_path.exists():
            logger.warning(f"Session file {session_path} does not exist")
            return False
        
        try:
            with open(session_path, 'r') as f:
                self.active_sessions[session_id] = json.load(f)
            return True
        except json.JSONDecodeError:
            logger.error(f"Error decoding session file {session_path}")
            return False
    
    def _load_all_sessions(self):
        """Load all sessions from disk."""
        for session_file in self.storage_dir.glob("*.json"):
            session_id = session_file.stem
            self._load_session(session_id)
    
    def cleanup_old_sessions(self, ttl=None):
        """Remove sessions older than TTL.
        
        Args:
            ttl: Time-to-live in seconds (default: self.message_ttl)
            
        Returns:
            int: Number of sessions removed
        """
        ttl = ttl or self.message_ttl
        now = datetime.now()
        removed_count = 0
        
        # Load all sessions
        self._load_all_sessions()
        
        for session_id, session_data in list(self.active_sessions.items()):
            updated_at = datetime.fromisoformat(session_data["updated_at"])
            age_seconds = (now - updated_at).total_seconds()
            
            if age_seconds > ttl:
                self.delete_session(session_id)
                removed_count += 1
        
        logger.info(f"Cleaned up {removed_count} old chat sessions")
        return removed_count


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
    
    def __init__(self, multi_ai_coordinator=None):
        """Initialize Minerva extensions.
        
        Args:
            multi_ai_coordinator: Optional MultiAICoordinator instance
        """
        self.chat_history = ChatHistory()
        self.web_researcher = WebResearcher()
        self.multi_ai_coordinator = multi_ai_coordinator
        self.active_sessions = {}
        
        logger.info("MinervaExtensions initialized")
    
    def process_message(self, message, session_id=None, model_preference=None, 
                        enable_web_research=False, research_depth="medium"):
        """Process a user message with enhanced capabilities.
        
        Args:
            message: User message
            session_id: Optional chat session ID
            model_preference: Optional model preference
            enable_web_research: Whether to enable web research
            research_depth: Web research depth (light, medium, deep)
            
        Returns:
            Dictionary with response data
        """
        # Create session if none provided
        if not session_id:
            session_id = self.chat_history.create_session()
        
        # Save user message to history
        message_id = self.chat_history.add_message(
            session_id, 
            message, 
            "user", 
            {"model_preference": model_preference, "enable_web_research": enable_web_research}
        )
        
        # Perform web research if enabled
        research_data = None
        if enable_web_research:
            logger.info(f"Performing web research for message {message_id}")
            research_data = self.web_researcher.research(message, depth=research_depth)
        
        # Process with coordinator based on model preference
        if self.multi_ai_coordinator:
            # Prepare additional args for the coordinator
            additional_args = {"message_id": message_id}
            
            # Add model override if specified
            if model_preference and model_preference != "blend":
                additional_args["model_override"] = model_preference
                additional_args["use_blending"] = False
            else:
                additional_args["use_blending"] = True
            
            # Add research data if available
            if research_data:
                additional_args["research_data"] = research_data
            
            # Process message with coordinator
            response = self.multi_ai_coordinator.process(message, **additional_args)
        else:
            # Simulate AI response if coordinator not available
            response = self._simulate_ai_response(message, model_preference, research_data)
        
        # Add research sources if available
        if research_data and "sources" in research_data:
            if isinstance(response, dict) and "model_info" in response:
                response["model_info"]["research_sources"] = [
                    {"title": source["title"], "url": source["url"]} 
                    for source in research_data["sources"]
                ]
            elif isinstance(response, str):
                # Convert string response to dict format
                response = {
                    "message": response,
                    "model_info": {
                        "research_sources": [
                            {"title": source["title"], "url": source["url"]} 
                            for source in research_data["sources"]
                        ]
                    }
                }
        
        # Ensure we have a consistent response format
        if isinstance(response, str):
            response = {"message": response}
        
        # Add response time
        if "model_info" not in response:
            response["model_info"] = {}
        response["model_info"]["response_time"] = f"{time.time() - time.time():.2f}s"
        
        # Save AI response to history
        response_content = response.get("message", str(response))
        self.chat_history.add_message(
            session_id, 
            response_content, 
            "ai", 
            response.get("model_info", {})
        )
        
        # Add session_id to response
        response["session_id"] = session_id
        
        return response
    
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


# Create singleton instance
minerva_extensions = MinervaExtensions()

# Try to connect extensions with MultiAICoordinator
try:
    from web.multi_ai_coordinator import multi_ai_coordinator
    minerva_extensions = MinervaExtensions(multi_ai_coordinator)
    logger.info("Successfully connected MinervaExtensions to MultiAICoordinator")
except ImportError:
    logger.warning("MultiAICoordinator not available, using simulated responses")
