#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minerva Web Server

This module implements a simple HTTP server that serves static files and handles API requests
for the Minerva interface.
"""

import sys
import os
import json
import logging
import uuid
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import traceback

# Add the parent directory to the path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Think Tank API handler
from think_tank_api import handle_think_tank_request

# Import the REAL Think Tank processor from the processor directory
from processor import think_tank

# Import necessary modules for model processing
import random
import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("minerva_server")

class MinervaRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler for Minerva that handles both static files and API requests."""
    
    def do_GET(self):
        """Handle GET requests for static files."""
        # Map root path to the Minerva central interface
        if self.path == '/':
            self.path = '/minerva_central.html'
        
        # Translate the path to be relative to the current directory
        # This allows the server to find files in the current directory
        # even when run from a parent directory
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests for API endpoints."""
        # Handle CORS preflight requests
        if self.command == 'OPTIONS':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Session-ID')
            self.end_headers()
            return
            
        parsed_path = urlparse(self.path)
        
        # API endpoints
        if parsed_path.path == "/api/think-tank":
            self.handle_think_tank_request()
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_think_tank_request(self):
        """Handle requests to the Think Tank API."""
        try:
            # Get request body size
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read and parse request body
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            # Process request using the Think Tank API handler
            # This provides a direct connection to the Think Tank without a bridge
            response_data = handle_think_tank_request(self, request_body)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Send the JSON response
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling Think Tank request: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Send error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "message": "An error occurred while processing your request",
                "error_details": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def generate_think_tank_response(self, message):
        """Generate a response from the Think Tank for the given message."""
        # Get conversation ID from request headers or generate a new one
        conversation_id = self.headers.get('X-Session-ID') or f"minerva-{uuid.uuid4()}"
        logger.info(f"Using conversation ID: {conversation_id}")
        
        # Check if this is a test request
        is_test_mode = 'X-Test-Mode' in self.headers
        if is_test_mode:
            logger.info("Test mode detected - will provide diagnostic information")
        
        # Colors for different models - consistent visual representation
        model_colors = {
            "gpt-4": "#10B981",    # Green
            "gpt-4o": "#06AED5",   # Teal
            "claude-3": "#6366F1", # Indigo
            "gemini": "#F59E0B",   # Amber
            "mistral": "#8B5CF6",  # Purple
            "llama-3": "#EC4899"   # Pink
        }
        
        try:
            # Process with the REAL Think Tank processor from processor/think_tank.py
            logger.info(f"Processing message with the real Think Tank processor: {message[:50]}...")
            
            # Enhanced query type detection
            query_tags = {}
            complexity = 0.7  # Default medium-high complexity
            
            # Detect technical queries
            if any(word in message.lower() for word in ["code", "function", "program", "algorithm", "class", "module"]):
                query_tags["technical"] = True
                query_tags["code"] = True
                query_tags["primary_domain"] = "technical"
                complexity = 0.8
            
            # Detect comparison queries
            elif any(word in message.lower() for word in ["compare", "difference", "versus", "vs", "better", "pros and cons"]):
                query_tags["comparison"] = True
                query_tags["primary_domain"] = "comparison"
                query_tags["primary_request"] = "comparison"
                complexity = 0.75
            
            # Detect creative queries
            elif any(word in message.lower() for word in ["creative", "story", "imagine", "fiction", "write a"]):
                query_tags["creative"] = True
                query_tags["primary_domain"] = "creative"
                complexity = 0.65
            
            # Detect explanation queries
            elif any(word in message.lower() for word in ["explain", "how", "why", "what is", "describe"]):
                query_tags["explanation"] = True
                query_tags["primary_domain"] = "explanation"
                query_tags["primary_request"] = "explanation"
                complexity = 0.7
            
            # Prioritized models based on capabilities from our MEMORIES
            available_models = [
                "gpt-4", "claude-3", "gemini", "mistral", "llama-3"
            ]
            
            # Process with the real Think Tank implementation
            result = think_tank.process_with_think_tank(
                message=message,
                model_priority=available_models,
                complexity=complexity,
                query_tags=query_tags
            )
            
            # Extract the key components from the Think Tank response
            model_responses = result.get('responses', {})
            processing_stats = result.get('processing_stats', {})
            query_metadata = result.get('query_metadata', {})
            errors = result.get('errors', {})
            
            # Get model rankings from processing stats or create default rankings
            model_rankings = []
            if 'model_rankings' in processing_stats:
                # Real rankings from processor
                model_rankings = processing_stats['model_rankings']
            else:
                # Create basic rankings based on models that responded
                for i, model_name in enumerate(model_responses.keys()):
                    # Higher score for earlier models (basic heuristic)
                    score = max(1.0, 10.0 - i)
                    model_rankings.append((model_name, score))
            
            # Determine the primary model (highest ranked)
            primary_model = model_rankings[0][0] if model_rankings else "unknown"
            
            # Get the response text - prioritize blended response if available
            response_text = None
            
            # First check if there's an explicit blended response
            if 'blended_response' in result and result['blended_response']:
                response_text = result['blended_response']
                logger.info("Using blended response from Think Tank processor")
            
            # If no blended response, use the primary model's response
            elif primary_model in model_responses:
                response_text = model_responses[primary_model]
                logger.info(f"Using primary model ({primary_model}) response")
            
            # Fall back to any available model response
            elif model_responses:
                # Use the first available model response
                fallback_model = next(iter(model_responses.keys()))
                response_text = model_responses[fallback_model]
                logger.info(f"Primary model unavailable, falling back to {fallback_model}")
            
            # Last resort error message
            if not response_text:
                response_text = "I'm sorry, but I couldn't process your request properly."
                logger.error("No valid response found in Think Tank results")
            
            # Determine the query type from metadata or query tags
            query_type = "general"
            if query_metadata.get('primary_domain'):
                query_type = query_metadata['primary_domain']
            elif query_tags.get('primary_domain'):
                query_type = query_tags['primary_domain']
            elif query_tags.get('technical'):
                query_type = "technical"
            elif query_tags.get('comparison'):
                query_type = "comparison"
            elif query_tags.get('explanation'):
                query_type = "explanation"
            elif query_tags.get('creative'):
                query_type = "creative"
            
            # Get blending strategy based on query type
            blending_strategy = query_type
            if query_metadata.get('is_comparison'):
                blending_strategy = "comparison"
            elif query_metadata.get('is_technical'):
                blending_strategy = "technical"
            
            # Created enhanced model info structure based on our MEMORIES implementation
            model_info = {
                "models_used": [],
                "primary_model": primary_model,
                "response_quality": processing_stats.get('quality_score', 8.5),
                "rankings": [],
                "query_analysis": {
                    "type": query_type,
                    "complexity": "high" if complexity > 0.7 else "medium",
                    "confidence": processing_stats.get('confidence', 0.85),
                    "detected_topics": query_metadata.get('domains', []),
                    "requires_creativity": query_type == "creative" or query_metadata.get('domains', []).count("creative") > 0,
                    "requires_technical": query_type == "technical" or query_metadata.get('is_technical', False)
                },
                "blending_strategy": blending_strategy,
                "blending_info": {
                    "strategy_name": f"{blending_strategy}_blend",
                    "quality": processing_stats.get('blending_quality', 0.9),
                    "sections_used": {}
                }
            }
            
            # Calculate total score for contribution percentage
            total_score = sum([score for _, score in model_rankings]) if model_rankings else 1.0
            
            # Add models_used information
            for model, score in model_rankings:
                # Calculate contribution percentage
                contribution = int(score * 100 / total_score) if total_score > 0 else 0
                
                # Get model color (or generate one if not predefined)
                color = model_colors.get(model.lower(), f"#{''.join(['%02X' % random.randint(0, 255) for _ in range(3)])}")
                
                # Get model strengths
                strengths = []
                if query_type == "technical" and model.lower() in ["gpt-4", "claude-3"]:
                    strengths.append("Strong technical reasoning")
                elif query_type == "creative" and model.lower() in ["claude-3", "gemini"]:
                    strengths.append("High creativity")
                elif query_type == "comparison" and model.lower() in ["gpt-4", "claude-3"]:
                    strengths.append("Balanced comparison")
                
                # Add model to models_used list
                model_info["models_used"].append({
                    "name": model,
                    "contribution": contribution,
                    "color": color,
                    "strengths": strengths
                })
            
            # Add detailed rankings with reasons
            for model, score in model_rankings:
                # Base score and capability boost based on model type
                base_score = score * 0.8  # 80% of score is base evaluation
                capability_boost = score * 0.2  # 20% from capability matching
                
                # Generate ranking reason based on query type
                reason = f"Selected for {query_type} query based on capabilities"
                if model == primary_model:
                    reason = f"Best performing model for {query_type} queries"
                
                # Identify model strengths
                strengths = []
                if model.lower() == "gpt-4":
                    strengths = ["Technical accuracy", "Reasoning", "Code quality"]
                elif model.lower() == "claude-3":
                    strengths = ["Detailed explanations", "Creative content", "Balanced perspective"] 
                elif model.lower() == "gemini":
                    strengths = ["Current information", "Diverse viewpoints", "Visual understanding"]
                elif model.lower() == "mistral":
                    strengths = ["Efficient processing", "Clear explanations"]
                
                # Identify weaknesses
                weaknesses = []
                if model.lower() not in ["gpt-4", "claude-3"] and query_type == "technical":
                    weaknesses = ["Less precise on technical details"]
                elif model.lower() not in ["claude-3", "gemini"] and query_type == "creative":
                    weaknesses = ["Less creative flourish"]
                
                # Add to rankings
                model_info["rankings"].append({
                    "model": model,
                    "score": score,
                    "base_score": base_score,
                    "capability_boost": capability_boost,
                    "reason": reason,
                    "strengths": strengths,
                    "weaknesses": weaknesses
                })
            
            # Add section contribution information based on MEMORIES implementation
            model_info["blending_info"]["sections_used"] = {
                "introduction": model_rankings[0][0] if len(model_rankings) > 0 else primary_model,
                "main_content": model_rankings[0][0] if len(model_rankings) > 0 else primary_model,
                "examples": model_rankings[1][0] if len(model_rankings) > 1 else primary_model,
                "additional_perspectives": model_rankings[2][0] if len(model_rankings) > 2 else primary_model
            }
            
            # Log successful processing
            logger.info(f"Successfully processed message with Think Tank: {len(model_responses)} models used")
            logger.info(f"Primary model: {primary_model}, Blending strategy: {blending_strategy}")
            
            # Create the complete API response with enhanced model_info structure
            return {
                "response": response_text,
                "model_info": model_info,
                "web_research": result.get('web_research'),
                "conversation_id": conversation_id,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in Think Tank processing: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a structured error response without mock data
            return {
                "response": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                "model_info": {
                    "error": str(e),
                    "error_details": traceback.format_exc()
                },
                "web_research": None,
                "conversation_id": conversation_id,
                "status": "error"
            }

def run_server(bind="0.0.0.0", port=8888):
    """Run the Minerva web server."""
    server_address = (bind, port)
    httpd = HTTPServer(server_address, MinervaRequestHandler)
    
    logger.info(f"Starting Minerva server on {bind}:{port}")
    logger.info(f"Open http://localhost:{port}/simplest_test.html in your browser")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Minerva web server")
    parser.add_argument("--bind", "-b", default="0.0.0.0", help="Specify the server hostname")
    parser.add_argument("--port", "-p", type=int, default=8888, help="Specify the server port")
    
    args = parser.parse_args()
    
    # Change to the correct directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    run_server(bind=args.bind, port=args.port)
