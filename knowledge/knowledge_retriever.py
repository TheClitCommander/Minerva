"""
Knowledge Retriever

This module handles the retrieval of knowledge from processed documents
using semantic search and other retrieval methods.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import numpy as np

# Base directory for knowledge storage
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_PROCESSED_DIR = BASE_DIR / "knowledge" / "processed"
DEFAULT_EMBEDDINGS_DIR = BASE_DIR / "knowledge" / "embeddings"

# Ensure default directories exist
DEFAULT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

def get_processed_dir() -> Path:
    """
    Get the processed documents directory path from environment variable or use default.
    
    This function checks for the PROCESSED_DIR environment variable and uses
    it if set, otherwise it falls back to the default './data/processed' path.
    The directory will be created if it doesn't exist.
    
    Returns:
        Path: The absolute path to the processed documents directory
    """
    dir_path = os.environ.get('PROCESSED_DIR', str(DEFAULT_PROCESSED_DIR))
    processed_dir = Path(dir_path)
    processed_dir = processed_dir.absolute()
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def get_embeddings_dir() -> Path:
    """
    Get the embeddings directory path from environment variable or use default.
    
    This function checks for the EMBEDDINGS_DIR environment variable and uses
    it if set, otherwise it falls back to the default './data/embeddings' path.
    The directory will be created if it doesn't exist.
    
    Returns:
        Path: The absolute path to the embeddings directory
    """
    dir_path = os.environ.get('EMBEDDINGS_DIR', str(DEFAULT_EMBEDDINGS_DIR))
    embeddings_dir = Path(dir_path)
    embeddings_dir = embeddings_dir.absolute()
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    return embeddings_dir

# For backward compatibility
PROCESSED_DIR = get_processed_dir()
EMBEDDINGS_DIR = get_embeddings_dir()

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    """Handles retrieval of knowledge from processed documents."""
    
    def __init__(self, embedding_model: Optional[str] = None):
        """
        Initialize the knowledge retriever.
        
        Args:
            embedding_model: Name or path of the embedding model to use
        """
        self.embedding_model = embedding_model
        self.embedder = None
        
        # Document cache for faster retrieval
        self.document_cache = {}
        self.embedding_cache = {}
        
        # Try to load embedding model if specified
        if embedding_model:
            try:
                self._load_embedding_model(embedding_model)
            except Exception as e:
                logger.warning(f"Could not load embedding model: {str(e)}")
    
    def _load_embedding_model(self, model_name_or_path: str) -> None:
        """
        Load the embedding model.
        
        Args:
            model_name_or_path: Name or path of the model to load
        """
        try:
            # First try loading as a HuggingFace model
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer(model_name_or_path)
            logger.info(f"Loaded embedding model: {model_name_or_path}")
        except ImportError:
            logger.warning("sentence-transformers not installed. Falling back to simpler methods.")
            self.embedder = None
    
    def retrieve(self, 
                query: str, 
                top_k: int = 5, 
                filters: Optional[Dict[str, Any]] = None,
                user_id: Optional[str] = None,
                user_preferences: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks for a query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            filters: Optional filters to apply to the search
            user_id: Optional user identifier to apply personalized settings
            user_preferences: Optional user preferences to override defaults
            
        Returns:
            results: List of relevant knowledge chunks with metadata
        """
        # Load all available documents and embeddings
        self._load_all_documents()
        
        # Apply user preferences if provided
        if user_preferences:
            # Override top_k based on user preferences
            top_k = user_preferences.get('top_k', top_k)
        elif user_id:
            # Try to load user preferences
            try:
                # Dynamically import to avoid circular imports
                from users.user_preference_manager import user_preference_manager
                params = user_preference_manager.get_retrieval_params(user_id)
                
                # Override top_k based on user preferences
                top_k = params.get('top_k', top_k)
                
                # Log the customization
                logger.info(f"Applied user {user_id} preferences to retrieval: top_k={top_k}")
            except Exception as e:
                logger.warning(f"Failed to apply user preferences: {str(e)}")
        
        # If we have an embedder, use semantic search
        if self.embedder:
            results = self._semantic_search(query, top_k, filters)
        else:
            # Fall back to keyword search
            results = self._keyword_search(query, top_k, filters)
        
        # Post-process results based on user preferences
        if user_preferences:
            max_tokens = user_preferences.get('max_tokens_per_chunk', None)
            if max_tokens:
                for result in results:
                    if 'text' in result and len(result['text']) > max_tokens * 4:  # Approximate token to char ratio
                        result['text'] = result['text'][:max_tokens * 4] + '...'
        
        logger.info(f"Retrieved {len(results)} results for query: {query}")
        return results
    
    def _load_all_documents(self) -> None:
        """Load all available documents and embeddings into cache."""
        # Skip if already loaded
        if self.document_cache and self.embedding_cache:
            return
        
        processed_dir = get_processed_dir()
        embeddings_dir = get_embeddings_dir()
        
        # Load all processed documents
        for doc_file in processed_dir.glob("*.json"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    document_id = doc_data.get("document_id")
                    if document_id:
                        self.document_cache[document_id] = doc_data
            except Exception as e:
                logger.error(f"Error loading document {doc_file}: {str(e)}")
        
        # Load all embeddings
        for emb_file in embeddings_dir.glob("*.json"):  
            try:
                with open(emb_file, 'r', encoding='utf-8') as f:
                    emb_data = json.load(f)
                    document_id = emb_data.get("document_id")
                    if document_id:
                        self.embedding_cache[document_id] = emb_data
            except Exception as e:
                logger.error(f"Error loading embeddings {emb_file}: {str(e)}")
        
        logger.info(f"Loaded {len(self.document_cache)} documents and {len(self.embedding_cache)} embedding sets")
    
    def _semantic_search(self, 
                        query: str, 
                        top_k: int = 5, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: The search query
            top_k: Number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            results: List of relevant knowledge chunks with metadata
        """
        results = []
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query).tolist()
            
            # Calculate similarity with all document chunks
            chunk_similarities = []
            for doc_id, emb_data in self.embedding_cache.items():
                if doc_id not in self.document_cache:
                    continue
                
                doc_data = self.document_cache[doc_id]
                doc_chunks = doc_data.get("chunks", [])
                doc_embeddings = emb_data.get("embeddings", [])
                
                # Skip if no chunks or embeddings
                if not doc_chunks or not doc_embeddings or len(doc_chunks) != len(doc_embeddings):
                    continue
                
                # Apply filters if provided
                if filters and not self._apply_filters(doc_data, filters):
                    continue
                
                # Calculate cosine similarity for each chunk
                for i, (chunk, embedding) in enumerate(zip(doc_chunks, doc_embeddings)):
                    similarity = self._cosine_similarity(query_embedding, embedding)
                    chunk_similarities.append({
                        "document_id": doc_id,
                        "chunk_index": i,
                        "content": chunk,
                        "similarity": similarity,
                        "metadata": doc_data.get("metadata", {})
                    })
            
            # Sort by similarity and take top_k
            chunk_similarities.sort(key=lambda x: x["similarity"], reverse=True)
            results = chunk_similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            # Fall back to keyword search
            results = self._keyword_search(query, top_k, filters)
        
        return results
    
    def _keyword_search(self, 
                       query: str, 
                       top_k: int = 5, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search.
        
        Args:
            query: The search query
            top_k: Number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            results: List of relevant knowledge chunks with metadata
        """
        results = []
        
        # Prepare query terms
        query_terms = [term.lower() for term in query.split()]
        
        # Score each document chunk based on term frequency
        chunk_scores = []
        for doc_id, doc_data in self.document_cache.items():
            # Apply filters if provided
            if filters and not self._apply_filters(doc_data, filters):
                continue
            
            doc_chunks = doc_data.get("chunks", [])
            metadata = doc_data.get("metadata", {})
            
            for i, chunk in enumerate(doc_chunks):
                # Calculate simple score based on term frequency
                chunk_lower = chunk.lower()
                score = sum(chunk_lower.count(term) for term in query_terms)
                
                # Add document info to results if it has a non-zero score
                if score > 0:
                    chunk_scores.append({
                        "document_id": doc_id,
                        "chunk_index": i,
                        "content": chunk,
                        "similarity": score,  # Using score as similarity
                        "metadata": metadata
                    })
        
        # Sort by score and take top_k
        chunk_scores.sort(key=lambda x: x["similarity"], reverse=True)
        results = chunk_scores[:top_k]
        
        return results
    
    def _apply_filters(self, doc_data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Apply filters to document data.
        
        Args:
            doc_data: Document data to filter
            filters: Filters to apply
            
        Returns:
            passes_filter: Whether the document passes the filters
        """
        metadata = doc_data.get("metadata", {})
        
        for key, value in filters.items():
            # Skip if key not in metadata
            if key not in metadata:
                return False
            
            # Check if value matches
            meta_value = metadata[key]
            
            # Handle different filter types
            if isinstance(value, list):
                # List filter - any value in list should match
                if meta_value not in value:
                    return False
            elif isinstance(value, dict):
                # Dictionary filter with operators
                for op, op_value in value.items():
                    if op == "eq" and meta_value != op_value:
                        return False
                    elif op == "neq" and meta_value == op_value:
                        return False
                    elif op == "gt" and not meta_value > op_value:
                        return False
                    elif op == "lt" and not meta_value < op_value:
                        return False
                    elif op == "gte" and not meta_value >= op_value:
                        return False
                    elif op == "lte" and not meta_value <= op_value:
                        return False
                    elif op == "in" and not meta_value in op_value:
                        return False
                    elif op == "nin" and meta_value in op_value:
                        return False
            else:
                # Direct value comparison
                if meta_value != value:
                    return False
        
        return True
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            similarity: Cosine similarity
        """
        # Convert to numpy arrays
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # Avoid division by zero
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
        
        return dot_product / (norm_vec1 * norm_vec2)

# Main function for testing
def main():
    """Test the knowledge retriever with sample data."""
    retriever = KnowledgeRetriever()
    
    # Test retrieval
    query = "sample document testing"
    results = retriever.retrieve(query, top_k=3)
    
    # Print results
    print(f"Query: {query}")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Document: {result['document_id']}")
        print(f"Similarity: {result['similarity']}")
        print(f"Content: {result['content'][:100]}...")

if __name__ == "__main__":
    main()
