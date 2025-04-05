#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Think Tank API Server

This is a simplified version of the Think Tank server that bypasses the complex processing
and directly returns responses from the models.
"""

import sys
import os
import logging
import uuid
import time
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# FastAPI for the server
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("simple_think_tank_api")

# Initialize FastAPI app
app = FastAPI(
    title="Simple Minerva Think Tank API",
    description="Simplified API server for Minerva's Think Tank mode.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI for direct model access
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    _OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI API initialized")
except ImportError:
    logger.warning("❌ OpenAI module not available")
    _OPENAI_AVAILABLE = False

# Define the request model
class ThinkTankRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(None, description="Conversation ID for tracking")
    store_in_memory: Optional[bool] = Field(False, description="Whether to store in memory")
    
# Define the endpoint
@app.post("/api/think-tank")
async def think_tank_endpoint(request: Request, think_tank_request: ThinkTankRequest, x_session_id: Optional[str] = Header(None)):
    """Process a message using Minerva's Think Tank mode."""
    start_time = time.time()
    
    try:
        logger.info(f"Processing message: {think_tank_request.message}")
        
        # Generate conversation ID if not provided
        conversation_id = think_tank_request.conversation_id or f"conv-{uuid.uuid4()}"
        
        # Use OpenAI to generate a response
        if _OPENAI_AVAILABLE:
            try:
                chat_completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are Minerva, an intelligent assistant with expertise across many domains. Provide a clear, accurate and helpful response."},
                        {"role": "user", "content": think_tank_request.message}
                    ],
                    temperature=0.7,
                )
                
                response_text = chat_completion.choices[0].message.content
                model_used = "gpt-4"
                
                logger.info(f"Generated response with {model_used}")
            except Exception as e:
                logger.error(f"Error with OpenAI: {str(e)}")
                # Fallback response
                response_text = "I'm sorry, I encountered an issue with the AI processing. Please try again."
                model_used = "fallback"
        else:
            # Fallback if OpenAI not available
            response_text = "Minerva's Think Tank is currently running in test mode. OpenAI API is not available."
            model_used = "test"
        
        # Prepare the response
        response_data = {
            "response": response_text,
            "model_info": {
                "models_used": [model_used],
                "rankings": {model_used: 1.0},
                "blending": {
                    "method": "direct",
                    "contributing_models": [model_used],
                }
            },
            "conversation_id": conversation_id,
            "processing_stats": {
                "time_taken": time.time() - start_time,
                "models_used": 1
            },
            "status": "success"
        }
        
        return JSONResponse(content=response_data)
    
    except Exception as e:
        logger.error(f"Error processing Think Tank request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error processing Think Tank request",
                "error_details": str(e)
            }
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify the API server is running."""
    return {
        "status": "ok", 
        "service": "Simple Minerva Think Tank API",
        "models": ["gpt-4"] if _OPENAI_AVAILABLE else ["test"],
        "api_keys_status": {"openai": "available" if _OPENAI_AVAILABLE else "missing"}
    }

# Main entry point for running the server
if __name__ == "__main__":
    logger.info("Starting Simple Minerva Think Tank API server...")
    uvicorn.run(
        "simple_think_tank_server:app", 
        host="0.0.0.0", 
        port=8099,
        reload=True
    )
