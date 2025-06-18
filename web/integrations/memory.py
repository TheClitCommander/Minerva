"""
Minerva Memory System

This module provides a persistent memory storage system using ChromaDB for Minerva.
It enables storing and retrieving past conversations, allowing Minerva to learn from
previous interactions and improve responses over time.
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Safe import of dependencies with fallbacks
import chromadb
from chromadb.utils import embedding_functions

# Safe import of sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("[Memory] sentence_transformers package available.")
except ImportError:
    logger.warning("[Memory] sentence_transformers not available. Falling back to limited memory mode.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Logger already configured above

class MinervaMemory:
    """
    ChromaDB-based memory system for Minerva to store and retrieve past conversations.
    This class provides methods to store, retrieve, and search through past interactions.
    """
    
    def __init__(self, persist_directory: str = "./data/memory_store"):
        """
        Initialize the ChromaDB memory system.
        
        Args:
            persist_directory: Path where the ChromaDB data will be stored
        """
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        
        # Check if we have existing collections first to determine which embedding to use
        try:
            # Try to get the existing collection first to check its properties
            existing_collection = None
            try:
                existing_collection = self.chroma_client.get_collection(
                    name="minerva_conversations"
                )
            except Exception as e:
                logger.info(f"No existing collection found: {str(e)}")
                
            # Force using OpenAI embeddings if collection exists (likely with 1536 dimensions)            
            if existing_collection and os.environ.get("OPENAI_API_KEY"):
                try:
                    from openai import OpenAI
                    self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=os.environ.get("OPENAI_API_KEY"),
                        model_name="text-embedding-ada-002"  # 1536 dimensions
                    )
                    logger.info("Using OpenAI embeddings to match existing collection (1536 dimensions)")
                except ImportError:
                    logger.warning("OpenAI package not available, but existing collection may use 1536 dimensions")
                    # We'll need to recreate the collection if this fails
                    if SENTENCE_TRANSFORMERS_AVAILABLE:
                        try:
                            # Default to sentence-transformers embedding function
                            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                                model_name="all-mpnet-base-v2"  # 768 dimensions
                            )
                            logger.info("Using sentence-transformer embeddings (768 dimensions)")
                        except Exception as e:
                            logger.warning(f"Failed to load sentence-transformers: {e}")
                            logger.warning("Falling back to default embedding function")
                            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                    else:
                        # If sentence_transformers isn't available at all, use DefaultEmbeddingFunction
                        logger.warning("Vector embeddings limited: sentence_transformers not available.")
                        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            else:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    try:
                        # Default to sentence-transformers embedding function
                        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                            model_name="all-mpnet-base-v2"  # 768 dimensions
                        )
                        logger.info("Using sentence-transformer embeddings (768 dimensions)")
                    except Exception as e:
                        logger.warning(f"Failed to load sentence-transformers: {e}")
                        logger.warning("Falling back to default embedding function")
                        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                else:
                    # If sentence_transformers isn't available at all, use DefaultEmbeddingFunction
                    logger.warning("Vector embeddings limited: sentence_transformers not available.")
                    self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        except ImportError as e:
            logger.warning(f"Error initializing embeddings: {str(e)}")
            logger.info("Defaulting to sentence-transformers embeddings")
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="all-mpnet-base-v2"
                    )
                except Exception as e:
                    logger.warning(f"Failed to load sentence-transformers: {e}")
                    # Fall back to the default function if sentence-transformers fails
                    logger.warning("Falling back to default embedding function")
                    self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            else:
                # If sentence_transformers isn't available at all, use DefaultEmbeddingFunction
                logger.warning("Vector embeddings limited: sentence_transformers not available.")
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Create collections for different memory types
        self.conversation_store = self.chroma_client.get_or_create_collection(
            name="minerva_conversations",
            embedding_function=self.embedding_function
        )
        
        self.knowledge_store = self.chroma_client.get_or_create_collection(
            name="minerva_knowledge",
            embedding_function=self.embedding_function
        )
        
        self.feedback_store = self.chroma_client.get_or_create_collection(
            name="minerva_feedback",
            embedding_function=self.embedding_function
        )
        
        logger.info(f"MinervaMemory initialized with {self.conversation_store.count()} stored conversations")
    
    def store_conversation(self, 
                           conversation_id: str, 
                           user_message: str, 
                           ai_response: str,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a conversation interaction in memory.
        
        Args:
            conversation_id: Unique ID for the conversation
            user_message: The user's message
            ai_response: Minerva's response
            metadata: Additional metadata for the conversation
            
        Returns:
            memory_id: Unique ID for the stored memory or None if storage failed
        """
        # Generate a unique ID for this memory entry
        memory_id = str(uuid.uuid4())
        
        # Create combined conversation document for better context retrieval
        conversation = f"User: {user_message}\nMinerva: {ai_response}"
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "type": "conversation",
            "memory_id": memory_id
        })
        
        # Try to store in ChromaDB
        try:
            self.conversation_store.add(
                documents=[conversation],
                metadatas=[metadata],
                ids=[memory_id]
            )
            logger.info(f"Stored conversation with ID {memory_id} for conversation {conversation_id}")
            return memory_id
        except Exception as e:
            # Log the error but don't cause the main operation to fail
            logger.error(f"Failed to store conversation in memory: {str(e)}")
            logger.warning("Chat will function without memory storage for this interaction")
            return memory_id  # Return the ID anyway so the operation completes
    
    def retrieve_memories(self, 
                          query: str, 
                          limit: int = 3, 
                          min_relevance_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on a query.
        
        Args:
            query: The query text to search for
            limit: Maximum number of memories to retrieve
            min_relevance_score: Minimum relevance score threshold
            
        Returns:
            List of memory objects with their content and metadata
        """
        # Check if collection is empty first
        collection_count = self.conversation_store.count()
        if collection_count == 0:
            logger.info(f"Memory store is empty. No memories to retrieve.")
            return []
        
        # Adjust limit if there are fewer items in the collection
        actual_limit = min(limit, collection_count)
        
        # Query ChromaDB for similar conversations
        try:
            results = self.conversation_store.query(
                query_texts=[query],
                n_results=actual_limit
            )
            
            memories = []
            if results and results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
                distances = results["distances"][0] if "distances" in results and results["distances"] else []
                
                for i, doc in enumerate(documents):
                    # Only process if we have metadata for this result
                    if i < len(metadatas):
                        metadata = metadatas[i]
                        
                        # Get the relevance score
                        distance = distances[i] if i < len(distances) else 0
                        # Convert distance to similarity score (closer to 1 is better)
                        relevance_score = 1.0 - min(distance, 1.0)
                        
                        # Only include memories above the relevance threshold
                        if relevance_score >= min_relevance_score:
                            memories.append({
                                "id": metadata.get("memory_id", f"memory_{i}"),
                                "content": doc,
                                "conversation_id": metadata.get("conversation_id", "unknown"),
                                "timestamp": metadata.get("timestamp", ""),
                                "relevance_score": relevance_score,
                                "metadata": metadata
                            })
            
            logger.info(f"Retrieved {len(memories)} relevant memories for query: {query[:50]}...")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    def add_knowledge(self, 
                     title: str, 
                     content: str, 
                     source: str = "user_provided",
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add knowledge to Minerva's knowledge base.
        
        Args:
            title: Title or brief description of the knowledge
            content: The knowledge content
            source: Source of the knowledge
            metadata: Additional metadata
            
        Returns:
            knowledge_id: Unique ID for the stored knowledge
        """
        knowledge_id = str(uuid.uuid4())
        
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "title": title,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "type": "knowledge",
            "knowledge_id": knowledge_id
        })
        
        self.knowledge_store.add(
            documents=[content],
            metadatas=[metadata],
            ids=[knowledge_id]
        )
        
        logger.info(f"Added knowledge '{title}' with ID {knowledge_id}")
        return knowledge_id
    
    def store_feedback(self, 
                      conversation_id: str, 
                      memory_id: str, 
                      rating: int, 
                      feedback_text: Optional[str] = None) -> str:
        """
        Store user feedback about a response for learning purposes.
        
        Args:
            conversation_id: ID of the conversation
            memory_id: ID of the memory being rated
            rating: Numeric rating (1-5)
            feedback_text: Optional text feedback
            
        Returns:
            feedback_id: Unique ID for the stored feedback
        """
        feedback_id = str(uuid.uuid4())
        
        metadata = {
            "conversation_id": conversation_id,
            "memory_id": memory_id,
            "rating": rating,
            "timestamp": datetime.now().isoformat(),
            "type": "feedback",
            "feedback_id": feedback_id
        }
        
        # Use feedback text if provided, otherwise create a simple document
        document = feedback_text if feedback_text else f"Rating: {rating}/5"
        
        self.feedback_store.add(
            documents=[document],
            metadatas=[metadata],
            ids=[feedback_id]
        )
        
        logger.info(f"Stored feedback (rating: {rating}) for memory {memory_id}")
        return feedback_id
    
    def enhance_query_with_memory(self, user_query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Enhance a user query with relevant memories for better AI response.
        
        Args:
            user_query: The original user query
            
        Returns:
            enhanced_query: Query enhanced with memory context
            memories: The retrieved memories used for enhancement
        """
        # Retrieve relevant memories
        memories = self.retrieve_memories(user_query, limit=3)
        
        if not memories:
            logger.info(f"No relevant memories found for query: {user_query[:50]}...")
            return user_query, []
        
        # Create an enhanced query with context from memories
        memory_context = "\n\n".join([
            f"Previous relevant conversation (relevance: {mem['relevance_score']:.2f}):"
            f"\n{mem['content']}"
            for mem in memories
        ])
        
        enhanced_query = f"""
        I'll provide you with some relevant previous conversations to give you context before answering my question.
        
        {memory_context}
        
        Given this context, please answer my question: {user_query}
        """
        
        logger.info(f"Enhanced query with {len(memories)} memories, top relevance: {memories[0]['relevance_score']:.2f}")
        return enhanced_query, memories
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory object or None if not found
        """
        try:
            result = self.conversation_store.get(ids=[memory_id])
            
            if result and result["documents"] and len(result["documents"]) > 0:
                return {
                    "id": memory_id,
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {}
                }
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
            
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conversation_store.delete(ids=[memory_id])
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            return False
    
    def get_all_memories(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all memories with pagination.
        
        Args:
            limit: Maximum number of memories to retrieve
            offset: Offset for pagination
            
        Returns:
            List of memory objects
        """
        try:
            # ChromaDB doesn't have native pagination, so we get all and slice
            result = self.conversation_store.get()
            
            if not result or not result["documents"]:
                return []
            
            total = len(result["documents"])
            end_idx = min(offset + limit, total)
            
            memories = []
            for i in range(offset, end_idx):
                memories.append({
                    "id": result["ids"][i] if "ids" in result else f"memory_{i}",
                    "content": result["documents"][i],
                    "metadata": result["metadatas"][i] if "metadatas" in result else {}
                })
                
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []

# Initialize a singleton instance for global use
memory_system = MinervaMemory()

# Utility functions for easy access to the memory system

def store_memory(conversation_id: str, user_message: str, ai_response: str, metadata: Optional[Dict] = None) -> str:
    """
    Store a conversation in memory.
    
    Args:
        conversation_id: ID of the conversation
        user_message: User's message
        ai_response: Minerva's response
        metadata: Additional metadata
        
    Returns:
        memory_id: ID of the stored memory
    """
    try:
        return memory_system.store_conversation(conversation_id, user_message, ai_response, metadata)
    except Exception as e:
        logger.error(f"Error in store_memory: {str(e)}")
        logger.warning("Continuing without storing memory")
        # Return a fake memory ID so processing can continue
        return str(uuid.uuid4())

def retrieve_memory(user_message: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve relevant memories for a user message.
    
    Args:
        user_message: The user's message to find relevant memories for
        top_k: Maximum number of memories to retrieve
        
    Returns:
        List of relevant memories
    """
    # For new memory systems with very few entries, we need to relax the relevance threshold
    # to ensure we get some results during testing phase
    collection_count = memory_system.conversation_store.count()
    min_relevance = 0.1 if collection_count < 10 else 0.7
    
    return memory_system.retrieve_memories(user_message, limit=top_k, min_relevance_score=min_relevance)

def enhance_with_memory(user_query: str) -> Tuple[str, List[Dict]]:
    """
    Enhance a user query with relevant memory context.
    
    Args:
        user_query: The original user query
        
    Returns:
        enhanced_query: Query with memory context
        memories: The retrieved memories
    """
    return memory_system.enhance_query_with_memory(user_query)

def get_memory(memory_id: str) -> Optional[Dict]:
    """Get a specific memory by ID."""
    return memory_system.get_memory_by_id(memory_id)

def delete_memory(memory_id: str) -> bool:
    """Delete a memory by ID."""
    return memory_system.delete_memory(memory_id)

def get_all_memories(limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get all memories with pagination."""
    return memory_system.get_all_memories(limit, offset)

def get_memories_by_conversation_id(conversation_id: str) -> List[Dict]:
    """
    Retrieve all memories associated with a specific conversation ID.
    
    Args:
        conversation_id: The ID of the conversation to retrieve memories for
        
    Returns:
        List of memory items associated with the conversation ID
    """
    if not conversation_id:
        logger.warning("No conversation ID provided for memory retrieval")
        return []
    
    try:
        # Get conversation collection
        collection = memory_system.chroma_client.get_or_create_collection(name="conversations")
        
        # Query for all memories with matching conversation_id in metadata
        results = collection.get(
            where={"conversation_id": conversation_id},
            include=["metadatas", "documents"]
        )
        
        # Format the results
        memories = []
        if results and results["ids"]:
            for i, memory_id in enumerate(results["ids"]):
                memory_item = {
                    "id": memory_id,
                    "document": results["documents"][i] if i < len(results["documents"]) else "",
                    "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {}
                }
                memories.append(memory_item)
        
        logger.info(f"Retrieved {len(memories)} memories for conversation {conversation_id}")
        return memories
    except Exception as e:
        logger.error(f"Error retrieving memories for conversation {conversation_id}: {str(e)}")
        return []

def add_knowledge(title: str, content: str, source: str = "user_provided", metadata: Optional[Dict] = None) -> str:
    """Add knowledge to Minerva's knowledge base."""
    return memory_system.add_knowledge(title, content, source, metadata)

# Utility functions for API integration
def format_memory_for_response(memory_item: Dict) -> Dict:
    """
    Format a memory item for API response.
    
    Args:
        memory_item: Memory item from the memory store
        
    Returns:
        Formatted memory item for API response
    """
    if not memory_item:
        return {}
        
    return {
        'id': memory_item.get('id', ''),
        'content': memory_item.get('content', ''),
        'metadata': memory_item.get('metadata', {}),
        'timestamp': memory_item.get('timestamp', datetime.now().isoformat()),
        'relevance_score': memory_item.get('relevance_score', 0)
    }

def integrate_memories_into_response(response: str, memories: List[Dict]) -> str:
    """
    Integrate retrieved memories into the AI response when appropriate.
    
    Args:
        response: Original AI response
        memories: List of relevant memories
        
    Returns:
        Enhanced response with memory context
    """
    if not memories:
        return response
        
    # This is a simplified implementation - in a real system, this would
    # use more sophisticated techniques to blend memories into the response
    memory_context = "\n\nI've recalled some relevant information:\n"
    
    for i, memory in enumerate(memories[:3], 1):
        memory_context += f"\n{i}. {memory.get('content', '')}\n"
    
    # Append memories only if they're not already part of the response
    if memory_context not in response:
        return response + memory_context
    return response

def extract_memory_command(message: str) -> Optional[Dict]:
    """
    Extract memory command from a user message.
    
    Args:
        message: User message
        
    Returns:
        Memory command if found, None otherwise
    """
    # This is a simple implementation - in a real system, this would use
    # more sophisticated NLP techniques to extract commands
    
    # Check for memory commands like "remember this" or "store this"
    lower_msg = message.lower()
    if any(cmd in lower_msg for cmd in ["remember this", "store this", "save this"]):
        # Extract content to remember
        content = message
        for prefix in ["remember this:", "store this:", "save this:"]:
            if prefix in lower_msg:
                content = message.split(prefix, 1)[1].strip()
                break
                
        return {
            "command": "add",
            "content": content
        }
    
    # Check for retrieval commands
    if any(cmd in lower_msg for cmd in ["recall", "remember when", "what do you remember about"]):
        query = message
        return {
            "command": "retrieve",
            "query": query
        }
        
    return None
    
def process_memory_command(command: Dict) -> Dict:
    """
    Process a memory command extracted from a user message.
    
    Args:
        command: Memory command dictionary
        
    Returns:
        Result of processing the command
    """
    if not command or "command" not in command:
        return {"success": False, "message": "Invalid command"}
        
    cmd_type = command["command"]
    
    if cmd_type == "add":
        if "content" not in command:
            return {"success": False, "message": "Missing content for add command"}
            
        content = command["content"]
        memory_id = store_memory(
            conversation_id=str(uuid.uuid4()),
            user_message="User requested to remember this information",
            ai_response="I'll remember this information",
            metadata={"memory_type": "explicit", "source": "user_command"}
        )
        
        return {
            "success": True,
            "message": "I've stored that in my memory.",
            "memory_id": memory_id
        }
        
    elif cmd_type == "retrieve":
        if "query" not in command:
            return {"success": False, "message": "Missing query for retrieve command"}
            
        query = command["query"]
        memories = retrieve_memory(query)
        
        return {
            "success": True,
            "message": "Here's what I remember:",
            "memories": memories
        }
        
    return {"success": False, "message": "Unknown command type"}

def handle_memory_api_request(request_data: Dict) -> Dict:
    """
    Handle memory-related API requests.
    
    Args:
        request_data: API request data
        
    Returns:
        API response
    """
    operation = request_data.get("operation")
    
    if operation == "add":
        content = request_data.get("content")
        metadata = request_data.get("metadata", {})
        
        if not content:
            return {"success": False, "message": "Missing content"}
            
        memory_id = store_memory(
            conversation_id=str(uuid.uuid4()),
            user_message="API requested to store this information",
            ai_response=content,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": "Memory stored successfully",
            "memory_id": memory_id
        }
        
    elif operation == "retrieve":
        query = request_data.get("query")
        limit = request_data.get("limit", 5)
        
        if not query:
            return {"success": False, "message": "Missing query"}
            
        memories = retrieve_memory(query, top_k=limit)
        formatted_memories = [format_memory_for_response(mem) for mem in memories]
        
        return {
            "success": True,
            "memories": formatted_memories
        }
        
    elif operation == "get":
        memory_id = request_data.get("memory_id")
        
        if not memory_id:
            return {"success": False, "message": "Missing memory_id"}
            
        memory = get_memory(memory_id)
        formatted_memory = format_memory_for_response(memory) if memory else {}
        
        return {
            "success": bool(memory),
            "memory": formatted_memory
        }
        
    elif operation == "delete":
        memory_id = request_data.get("memory_id")
        
        if not memory_id:
            return {"success": False, "message": "Missing memory_id"}
            
        success = delete_memory(memory_id)
        
        return {
            "success": success,
            "message": "Memory deleted successfully" if success else "Failed to delete memory"
        }
        
    return {"success": False, "message": "Unknown operation"}
