#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Think Tank API Server

This module implements a FastAPI server that provides API access to 
Minerva's Think Tank mode, connecting the web interface to the backend Think Tank processor.
"""

import sys
import os
import logging
import uuid
import time
import json
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# FastAPI for the server
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("think_tank_api")

# Import consolidated Think Tank processing module
from web.think_tank_consolidated import process_with_think_tank, get_model_status

# Import conversation database
try:
    from web.database.memory_bridge import get_memory_bridge
    memory_bridge = get_memory_bridge()
    MEMORY_AVAILABLE = True
    logger.info("✅ Conversation memory database initialized and ready")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize conversation memory: {str(e)}")
    MEMORY_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="Minerva Think Tank API",
    description="API server for Minerva's Think Tank mode, using a multi-model approach to generate optimized responses.",
    version="1.0.0"
)

# Configure CORS to allow requests from web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for the Think Tank API
class ThinkTankRequest:
    def __init__(self, request_data: Dict[str, Any]):
        self.message = request_data.get("message", "")
        self.conversation_id = request_data.get("conversation_id", str(uuid.uuid4()))
        self.model_preferences = request_data.get("model_preferences", {})
        self.store_in_memory = request_data.get("store_in_memory", True)
        self.context_depth = request_data.get("context_depth", 10)  # How many past messages to include

# API Routes
@app.post("/api/think-tank")
async def think_tank_endpoint(request: Request, x_session_id: Optional[str] = Header(None)):
    """
    Process a message using Minerva's Think Tank mode.
    
    This endpoint runs the message through multiple AI models, ranks their responses,
    and returns the best response along with detailed model information.
    """
    try:
        # Parse the request body
        request_data = await request.json()
        logger.info(f"Received Think Tank request: {request_data.get('message', '')[:50]}...")
        
        # Create a structured request object
        think_tank_request = ThinkTankRequest(request_data)
        
        # Track the session ID if provided
        session_id = x_session_id or think_tank_request.conversation_id
        logger.info(f"Processing with session ID: {session_id}")
        
        # Check if test mode is enabled via header
        test_mode = request.headers.get("X-Test-Mode", "false").lower() == "true"
        
        # Get conversation history if available
        conversation_history = []
        if MEMORY_AVAILABLE and think_tank_request.context_depth > 0:
            try:
                # Get conversation history limited by context depth
                conversation = memory_bridge.get_conversation(think_tank_request.conversation_id)
                if conversation:
                    # Only use the most recent messages based on context_depth
                    conversation_history = conversation[-think_tank_request.context_depth:] if len(conversation) > think_tank_request.context_depth else conversation
                    logger.info(f"Retrieved {len(conversation_history)} messages from conversation history")
            except Exception as e:
                logger.warning(f"Error retrieving conversation history: {str(e)}")
        
        # Store the user message in memory if enabled
        if MEMORY_AVAILABLE and think_tank_request.store_in_memory:
            try:
                memory_bridge.add_message(
                    think_tank_request.conversation_id,
                    "user",
                    think_tank_request.message
                )
                logger.info(f"Stored user message in conversation {think_tank_request.conversation_id}")
            except Exception as e:
                logger.warning(f"Error storing user message: {str(e)}")
        
        # Process the message with the Think Tank using our consolidated implementation
        result = process_with_think_tank(
            message=think_tank_request.message,
            conversation_id=think_tank_request.conversation_id,
            test_mode=test_mode
        )
        
        # Handle the case where result is None
        if result is None:
            logger.error(f"Think Tank returned None for message: {think_tank_request.message}")
            result = {}
        
        # Get the response text
        response_text = result.get("response", "I'm currently experiencing some difficulties processing your request. The AI models responded but the output formatter encountered an issue.")
        
        # Store the assistant response in memory if enabled
        if MEMORY_AVAILABLE and think_tank_request.store_in_memory and response_text:
            try:
                memory_bridge.add_message(
                    think_tank_request.conversation_id,
                    "assistant",
                    response_text
                )
                logger.info(f"Stored assistant response in conversation {think_tank_request.conversation_id}")
            except Exception as e:
                logger.warning(f"Error storing assistant response: {str(e)}")
        
        # Prepare the response
        response_data = {
            "response": response_text,
            "model_info": result.get("model_info", {}),
            "web_research": result.get("web_research", None),
            "conversation_id": think_tank_request.conversation_id,
            "status": "success",
            "memory_status": {
                "memory_enabled": MEMORY_AVAILABLE,
                "context_used": len(conversation_history) if 'conversation_history' in locals() else 0,
                "message_stored": think_tank_request.store_in_memory and MEMORY_AVAILABLE
            }
        }
        
        # Include detailed model data if requested or in test mode
        include_details = (
            test_mode or
            think_tank_request.model_preferences.get("include_detailed_rankings", False)
        )
        
        if not include_details and "detailed_rankings" in response_data.get("model_info", {}):
            del response_data["model_info"]["detailed_rankings"]
        
        logger.info(f"Think Tank processing completed successfully")
        return JSONResponse(content=response_data)
    
    except Exception as e:
        logger.error(f"Error processing Think Tank request: {str(e)}")
        logger.error(f"Stack trace: {logging.traceback.format_exc()}")
        
        # Return a structured error response
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An error occurred while processing your request",
                "error_details": str(e)
            }
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify the API server is running."""
    # Get model status information from the consolidated implementation
    model_status = get_model_status()
    
    return {
        "status": "ok", 
        "service": "Minerva Think Tank API",
        "models": model_status["available_models"],
        "api_models": model_status["api_models"],
        "api_keys_status": model_status["api_keys_status"]
    }

@app.post("/api/analyze-query")
async def analyze_query(request: Request):
    """Analyze a query to determine its type and the most suitable models.
    
    This endpoint provides transparency into how the Think Tank analyzes and routes queries.
    """
    try:
        request_data = await request.json()
        message = request_data.get("message", "")
        
        if not message.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Please provide a non-empty message to analyze"}
            )
            
        # Import the AI router directly for query analysis
        from processor.ai_router import route_request, get_query_tags
        
        # Get routing information and query tags
        routing_info = route_request(message)
        query_tags = get_query_tags(message)
        
        # Get model capabilities from the consolidated implementation
        model_status = get_model_status()
        
        return {
            "query": message,
            "analysis": {
                "routing": routing_info,
                "query_tags": query_tags,
            },
            "models": {
                "priority": routing_info["model_priority"],
                "available": model_status["available_models"],
                "api_status": model_status["api_keys_status"]
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error analyzing query: {str(e)}"}
        )

# Conversation history endpoints
@app.get("/api/conversations")
async def get_conversations(limit: int = 10, offset: int = 0):
    """Get a list of recent conversations with their summaries"""
    if not MEMORY_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Conversation memory system is not available"
            }
        )
        
    try:
        conversations = memory_bridge.get_recent_conversations(limit)
        return JSONResponse(content={
            "status": "success",
            "conversations": conversations,
            "count": len(conversations),
            "has_more": len(conversations) >= limit
        })
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error retrieving conversation history",
                "error_details": str(e)
            }
        )

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, context_depth: int = 0):
    """Get a specific conversation with its messages"""
    if not MEMORY_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Conversation memory system is not available"
            }
        )
        
    try:
        conversation = memory_bridge.get_conversation(conversation_id)
        if not conversation:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Conversation {conversation_id} not found"
                }
            )
            
        # If context depth is specified, limit the messages
        if context_depth > 0 and len(conversation) > context_depth:
            conversation = conversation[-context_depth:]
            
        # Get the conversation summary if available
        summary = memory_bridge.get_conversation_summary(conversation_id)
            
        return JSONResponse(content={
            "status": "success",
            "conversation_id": conversation_id,
            "messages": conversation,
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error retrieving conversation",
                "error_details": str(e)
            }
        )

@app.put("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, request: Request):
    """Update conversation metadata such as title"""
    if not MEMORY_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Conversation memory system is not available"
            }
        )
        
    try:
        request_data = await request.json()
        title = request_data.get("title")
        
        if not title:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Title is required"
                }
            )
            
        success = memory_bridge.update_conversation_title(conversation_id, title)
        
        if not success:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Conversation {conversation_id} not found"
                }
            )
            
        return JSONResponse(content={
            "status": "success",
            "message": "Conversation updated",
            "conversation_id": conversation_id
        })
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error updating conversation",
                "error_details": str(e)
            }
        )

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, permanent: bool = False):
    """Delete a conversation (soft delete by default)"""
    if not MEMORY_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Conversation memory system is not available"
            }
        )
        
    try:
        if permanent:
            success = memory_bridge.permanently_delete_conversation(conversation_id)
        else:
            success = memory_bridge.delete_conversation(conversation_id)
            
        if not success:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Conversation {conversation_id} not found"
                }
            )
            
        return JSONResponse(content={
            "status": "success",
            "message": f"Conversation {conversation_id} {'permanently ' if permanent else ''}deleted"
        })
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error deleting conversation",
                "error_details": str(e)
            }
        )

@app.get("/api/conversations/search/{query}")
async def search_conversations(query: str, limit: int = 10):
    """Search for conversations by content or title"""
    if not MEMORY_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Conversation memory system is not available"
            }
        )
        
    try:
        results = memory_bridge.search_conversations(query, limit)
        return JSONResponse(content={
            "status": "success",
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        logger.error(f"Error searching conversations: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error searching conversations",
                "error_details": str(e)
            }
        )

# Main entry point for running the server
if __name__ == "__main__":
    logger.info("Starting Minerva Think Tank API server...")
    uvicorn.run(
        "think_tank_server:app", 
        host="0.0.0.0", 
        port=8080,
        reload=True
    )
