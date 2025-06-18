"""
Enhanced Knowledge Management System

This module implements a RAG (Retrieval-Augmented Generation) system
that enhances Minerva's ability to retrieve and utilize relevant knowledge.
"""

import logging
import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple

# Import existing components to build upon
from ai_decision.context_decision_tree import decision_tree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeDocument:
    """Represents a retrievable knowledge document in the system"""
    
    def __init__(self, doc_id: str, title: str, content: str, 
                 source: str, metadata: Dict[str, Any] = None):
        """
        Initialize a knowledge document
        
        Args:
            doc_id: Unique identifier for this document
            title: Title of the document
            content: Full text content of the document
            source: Source of the document (e.g., "codebase", "documentation")
            metadata: Additional metadata about the document
        """
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.source = source
        self.metadata = metadata or {}
        self.embedding = None  # Will be computed when needed
        self.chunks = self._chunk_content()
        self.indexed_at = time.time()
    
    def _chunk_content(self, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split the content into overlapping chunks for more precise retrieval
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of chunks with position information
        """
        if not self.content:
            return []
            
        chunks = []
        content_len = len(self.content)
        
        for i in range(0, content_len, chunk_size - overlap):
            chunk_end = min(i + chunk_size, content_len)
            chunk_text = self.content[i:chunk_end]
            
            # Skip empty chunks
            if not chunk_text.strip():
                continue
                
            chunks.append({
                "position": len(chunks),
                "text": chunk_text,
                "start_char": i,
                "end_char": chunk_end,
                "embedding": None  # Will be computed when needed
            })
            
            # If we've reached the end of the content, break
            if chunk_end == content_len:
                break
                
        return chunks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "source": self.source,
            "metadata": self.metadata,
            "indexed_at": self.indexed_at,
            "chunk_count": len(self.chunks)
        }


class KnowledgeRepository:
    """Manages a collection of knowledge documents for retrieval"""
    
    def __init__(self):
        """Initialize the knowledge repository"""
        self.documents = {}  # doc_id -> KnowledgeDocument
        self.embedding_cache = {}  # (doc_id, chunk_position) -> embedding
        
        # Index by source and other metadata for filtering
        self.source_index = {}  # source -> [doc_id]
        self.keyword_index = {}  # keyword -> [doc_id]
        
        logger.info("Knowledge Repository initialized")
    
    def add_document(self, document: KnowledgeDocument) -> bool:
        """
        Add a document to the repository
        
        Args:
            document: The document to add
            
        Returns:
            True if the document was added successfully
        """
        if document.doc_id in self.documents:
            logger.warning(f"Document with ID {document.doc_id} already exists, updating")
            
        self.documents[document.doc_id] = document
        
        # Update source index
        if document.source not in self.source_index:
            self.source_index[document.source] = []
        self.source_index[document.source].append(document.doc_id)
        
        # Extract and index keywords from title and metadata
        keywords = self._extract_keywords(document)
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            self.keyword_index[keyword].append(document.doc_id)
        
        logger.info(f"Added document {document.doc_id} to repository")
        return True
    
    def _extract_keywords(self, document: KnowledgeDocument) -> List[str]:
        """
        Extract keywords from a document for indexing
        
        Args:
            document: The document to extract keywords from
            
        Returns:
            List of keywords
        """
        keywords = set()
        
        # Add words from title
        for word in document.title.lower().split():
            if len(word) > 3:  # Ignore very short words
                keywords.add(word)
        
        # Add relevant metadata as keywords
        if "tags" in document.metadata:
            for tag in document.metadata["tags"]:
                keywords.add(tag.lower())
                
        if "category" in document.metadata:
            keywords.add(document.metadata["category"].lower())
            
        if "project" in document.metadata:
            keywords.add(document.metadata["project"].lower())
        
        return list(keywords)
    
    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """
        Get a document by ID
        
        Args:
            doc_id: The ID of the document to get
            
        Returns:
            The document or None if not found
        """
        return self.documents.get(doc_id)
    
    def get_document_chunk(self, doc_id: str, position: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk from a document
        
        Args:
            doc_id: The ID of the document
            position: The position of the chunk
            
        Returns:
            The chunk or None if not found
        """
        document = self.get_document(doc_id)
        if not document:
            return None
            
        if position < 0 or position >= len(document.chunks):
            return None
            
        return document.chunks[position]
    
    def search_documents(self, query: str, filters: Dict[str, Any] = None, 
                        max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents matching a query
        
        Args:
            query: The search query
            filters: Optional filters to apply (source, metadata fields)
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        filters = filters or {}
        matched_docs = []
        
        # Filter by source if specified
        candidate_docs = []
        if "source" in filters:
            source_docs = self.source_index.get(filters["source"], [])
            for doc_id in source_docs:
                candidate_docs.append(self.documents[doc_id])
        else:
            candidate_docs = list(self.documents.values())
        
        # Apply other metadata filters
        if "metadata" in filters:
            for key, value in filters["metadata"].items():
                candidate_docs = [
                    doc for doc in candidate_docs 
                    if key in doc.metadata and doc.metadata[key] == value
                ]
        
        # Simple keyword matching for now
        # In a real implementation, this would use embeddings for semantic search
        query_terms = query.lower().split()
        for doc in candidate_docs:
            score = 0
            
            # Check title for matches
            title_lower = doc.title.lower()
            for term in query_terms:
                if term in title_lower:
                    score += 5  # Title matches are weighted higher
            
            # Check content snippets for matches
            for chunk in doc.chunks:
                chunk_text = chunk["text"].lower()
                for term in query_terms:
                    if term in chunk_text:
                        score += 1
            
            if score > 0:
                matched_docs.append({
                    "document": doc.to_dict(),
                    "score": score,
                    "matching_chunks": [
                        chunk["position"] for chunk in doc.chunks
                        if any(term in chunk["text"].lower() for term in query_terms)
                    ]
                })
        
        # Sort by score (descending)
        matched_docs.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top results
        return matched_docs[:max_results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the repository"""
        stats = {
            "total_documents": len(self.documents),
            "total_chunks": sum(len(doc.chunks) for doc in self.documents.values()),
            "sources": {},
            "indexed_keywords": len(self.keyword_index)
        }
        
        # Count documents by source
        for source, doc_ids in self.source_index.items():
            stats["sources"][source] = len(doc_ids)
        
        return stats


class KnowledgeEnhancedContext:
    """
    Uses retrieved knowledge to enhance context for AI decision making
    and better response generation.
    """
    
    def __init__(self, knowledge_repository: KnowledgeRepository):
        """
        Initialize the knowledge-enhanced context
        
        Args:
            knowledge_repository: Repository of knowledge documents
        """
        self.repository = knowledge_repository
        self.context_analyzer = decision_tree
        self.retrieval_cache = {}  # (query, filters_hash) -> retrieval_result
        
        logger.info("Knowledge Enhanced Context initialized")
    
    def _get_cache_key(self, query: str, filters: Dict[str, Any] = None) -> str:
        """Generate a cache key for a query and filters"""
        filters_str = json.dumps(filters, sort_keys=True) if filters else ""
        return f"{query}:{filters_str}"
    
    def enhance_context(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """
        Enhance context with relevant knowledge based on the user's message
        
        Args:
            message: The user's message
            user_id: Optional user ID for personalization
            
        Returns:
            Enhanced context dictionary
        """
        # Start with basic context analysis
        context = self.context_analyzer.analyze_context(message)
        
        # Extract potential search queries from the message
        search_queries = self._extract_search_queries(message, context)
        
        # Retrieve relevant documents for each query
        retrieved_documents = []
        for query, filters in search_queries:
            # Check cache first
            cache_key = self._get_cache_key(query, filters)
            if cache_key in self.retrieval_cache:
                query_results = self.retrieval_cache[cache_key]
            else:
                query_results = self.repository.search_documents(query, filters)
                # Cache the results
                self.retrieval_cache[cache_key] = query_results
            
            retrieved_documents.extend(query_results)
        
        # Deduplicate documents (same document might be returned for multiple queries)
        seen_docs = set()
        unique_documents = []
        for doc in retrieved_documents:
            doc_id = doc["document"]["doc_id"]
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_documents.append(doc)
        
        # Limit to top 3 most relevant documents
        top_documents = sorted(unique_documents, key=lambda x: x["score"], reverse=True)[:3]
        
        # Add retrieved knowledge to context
        knowledge_context = {
            "has_relevant_knowledge": len(top_documents) > 0,
            "relevant_documents": top_documents,
            "knowledge_summary": self._generate_knowledge_summary(top_documents)
        }
        
        # Merge with original context
        enhanced_context = {**context, "knowledge": knowledge_context}
        
        return enhanced_context
    
    def _extract_search_queries(self, message: str, context: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract potential search queries from a message
        
        Args:
            message: The user's message
            context: Basic context analysis
            
        Returns:
            List of (query, filters) tuples
        """
        queries = []
        
        # Use the full message as a query
        queries.append((message, None))
        
        # If the message is very long, use a truncated version
        if len(message) > 100:
            queries.append((message[:100], None))
        
        # If the message contains a question, extract it
        if "?" in message:
            for question in message.split("?"):
                if len(question) > 10:  # Only use substantial questions
                    queries.append((question, None))
        
        # For technical queries, search in code documentation
        if context.get("detail_level") == "technical":
            queries.append((message, {"source": "code_documentation"}))
        
        return queries
    
    def _generate_knowledge_summary(self, documents: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of retrieved knowledge
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            A summary string
        """
        if not documents:
            return "No relevant knowledge found."
        
        summary = "Relevant knowledge found:\n"
        
        for i, doc in enumerate(documents):
            document = doc["document"]
            summary += f"{i+1}. {document['title']} ({document['source']})\n"
        
        return summary
    
    def get_document_context(self, doc_id: str, chunk_position: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get context information for a specific document or chunk
        
        Args:
            doc_id: The document ID
            chunk_position: Optional chunk position
            
        Returns:
            Document context dictionary or None if not found
        """
        document = self.repository.get_document(doc_id)
        if not document:
            return None
        
        context = {
            "document": document.to_dict(),
            "full_content": False
        }
        
        if chunk_position is not None:
            chunk = self.repository.get_document_chunk(doc_id, chunk_position)
            if chunk:
                context["chunk"] = chunk
                context["content"] = chunk["text"]
            else:
                return None
        else:
            # If no specific chunk requested, include preview of first chunk
            if document.chunks:
                preview_chunk = document.chunks[0]
                context["preview"] = {
                    "position": preview_chunk["position"],
                    "text": preview_chunk["text"][:200] + "..." if len(preview_chunk["text"]) > 200 else preview_chunk["text"]
                }
                context["chunk_count"] = len(document.chunks)
        
        return context


class KnowledgeManager:
    """
    Main knowledge management system that integrates knowledge retrieval with
    AI response generation for comprehensive question answering.
    """
    
    def __init__(self):
        """Initialize the knowledge manager"""
        self.repository = KnowledgeRepository()
        self.context_enhancer = KnowledgeEnhancedContext(self.repository)
        self.import_history = {}
        
        logger.info("Knowledge Manager initialized")
    
    def import_knowledge_from_file(self, file_path: str, source: str, 
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Import knowledge from a file
        
        Args:
            file_path: Path to the file
            source: Source identifier
            metadata: Additional metadata
            
        Returns:
            Import result dictionary
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            file_name = os.path.basename(file_path)
            doc_id = f"{source}:{file_name}"
            
            document = KnowledgeDocument(
                doc_id=doc_id,
                title=file_name,
                content=content,
                source=source,
                metadata=metadata or {"file_path": file_path}
            )
            
            self.repository.add_document(document)
            
            self.import_history[doc_id] = {
                "file_path": file_path,
                "imported_at": time.time(),
                "source": source
            }
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": file_name,
                "chunk_count": len(document.chunks)
            }
        except Exception as e:
            logger.error(f"Error importing file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def import_knowledge_from_text(self, content: str, title: str, source: str, 
                                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Import knowledge from text content
        
        Args:
            content: The text content
            title: Title for the document
            source: Source identifier
            metadata: Additional metadata
            
        Returns:
            Import result dictionary
        """
        try:
            doc_id = f"{source}:{title.replace(' ', '_')}_{int(time.time())}"
            
            document = KnowledgeDocument(
                doc_id=doc_id,
                title=title,
                content=content,
                source=source,
                metadata=metadata or {}
            )
            
            self.repository.add_document(document)
            
            self.import_history[doc_id] = {
                "imported_at": time.time(),
                "source": source
            }
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "chunk_count": len(document.chunks)
            }
        except Exception as e:
            logger.error(f"Error importing text content: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def enhance_response_with_knowledge(self, message: str, response: str, 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance an AI response with relevant knowledge
        
        Args:
            message: The user's message
            response: The original AI response
            context: Context dictionary
            
        Returns:
            Enhanced response dictionary
        """
        enhanced_context = self.context_enhancer.enhance_context(message)
        
        # If we have relevant knowledge, use it to enhance the response
        knowledge_context = enhanced_context.get("knowledge", {})
        has_knowledge = knowledge_context.get("has_relevant_knowledge", False)
        
        if not has_knowledge:
            return {
                "enhanced_response": response,
                "has_knowledge_enhancement": False,
                "original_response": response
            }
        
        # In a real implementation, this would feed the knowledge into the AI
        # to generate an enhanced response. For now, we'll simulate this with
        # a simple prefix.
        documents = knowledge_context.get("relevant_documents", [])
        knowledge_prefix = "Based on my knowledge:\n\n"
        
        for i, doc in enumerate(documents[:2]):  # Use top 2 documents
            document = doc["document"]
            knowledge_prefix += f"From {document['title']}:\n"
            
            # Get content from matching chunks
            document_obj = self.repository.get_document(document["doc_id"])
            if document_obj and "matching_chunks" in doc:
                for chunk_pos in doc["matching_chunks"][:2]:  # Use top 2 chunks
                    if chunk_pos < len(document_obj.chunks):
                        chunk = document_obj.chunks[chunk_pos]
                        # Add a snippet from the chunk
                        snippet = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                        knowledge_prefix += f"- {snippet}\n\n"
        
        # Combine the knowledge with the original response
        enhanced_response = f"{knowledge_prefix}\n{response}"
        
        return {
            "enhanced_response": enhanced_response,
            "has_knowledge_enhancement": True,
            "original_response": response,
            "knowledge_summary": knowledge_context.get("knowledge_summary", ""),
            "document_references": [doc["document"]["doc_id"] for doc in documents]
        }
    
    def search_knowledge(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search the knowledge repository
        
        Args:
            query: The search query
            filters: Optional filters to apply
            
        Returns:
            List of search results
        """
        return self.repository.search_documents(query, filters)
    
    def get_import_history(self) -> Dict[str, Any]:
        """Get the knowledge import history"""
        return self.import_history
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge repository"""
        return self.repository.get_statistics()


# Create a singleton instance
knowledge_manager = KnowledgeManager()

def initialize_with_sample_data():
    """Initialize the knowledge manager with sample data for testing"""
    # Add some sample documents
    knowledge_manager.import_knowledge_from_text(
        content="""
        Python is a high-level, interpreted programming language known for its readability
        and versatility. It supports multiple programming paradigms, including procedural,
        object-oriented, and functional programming. Python is widely used in web development,
        data science, artificial intelligence, and automation.
        
        Key features of Python:
        - Simple, readable syntax
        - Dynamic typing
        - Automatic memory management
        - Extensive standard library
        - Large ecosystem of third-party packages
        """,
        title="Python Programming Language",
        source="documentation",
        metadata={"category": "programming", "tags": ["python", "programming"]}
    )
    
    knowledge_manager.import_knowledge_from_text(
        content="""
        Artificial Intelligence (AI) refers to the simulation of human intelligence in machines
        that are programmed to think and learn like humans. The term may also be applied to any
        machine that exhibits traits associated with a human mind such as learning and problem-solving.
        
        Machine Learning (ML) is a subset of AI that enables systems to learn and improve from
        experience without being explicitly programmed. ML algorithms build a mathematical model
        based on sample data, known as training data, in order to make predictions or decisions
        without being explicitly programmed to perform the task.
        
        Deep Learning is a subset of ML that uses neural networks with many layers (hence the term "deep")
        to analyze various factors of data. Deep learning is what powers the most human-like AI.
        """,
        title="Artificial Intelligence and Machine Learning",
        source="documentation",
        metadata={"category": "ai", "tags": ["ai", "machine learning", "deep learning"]}
    )
    
    knowledge_manager.import_knowledge_from_text(
        content="""
        Minerva is an advanced AI assistant designed to provide comprehensive and accurate
        responses to a wide range of queries. It combines multiple AI models, context-aware
        decision making, and knowledge retrieval to deliver optimal results.
        
        Key components of Minerva:
        - Multi-AI Coordinator: Manages multiple AI models and selects the best one for each query
        - Context Decision Tree: Analyzes query context to determine optimal response parameters
        - Enhanced Memory System: Stores and retrieves knowledge for more accurate responses
        - Role-Based Architecture: Assigns specialized roles for different types of tasks
        - Workflow Automation: Handles complex multi-step tasks with structured workflows
        """,
        title="Minerva AI Assistant Overview",
        source="project_documentation",
        metadata={"category": "project", "tags": ["minerva", "system", "overview"]}
    )
    
    logger.info("Knowledge Manager initialized with sample data")


if __name__ == "__main__":
    # Example usage
    print("Testing Knowledge Management System")
    
    # Initialize with sample data
    initialize_with_sample_data()
    
    # Get repository stats
    stats = knowledge_manager.get_repository_stats()
    print(f"\nRepository Statistics: {json.dumps(stats, indent=2)}")
    
    # Test search
    search_queries = [
        "Python programming",
        "What is artificial intelligence?",
        "Minerva system components"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: {query}")
        results = knowledge_manager.search_knowledge(query)
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['document']['title']} (Score: {result['score']})")
    
    # Test context enhancement
    test_messages = [
        "How does Python handle memory management?",
        "What are the key components of Minerva?",
        "Explain the difference between AI and machine learning"
    ]
    
    for message in test_messages:
        print(f"\n\nEnhancing context for message: {message}")
        enhanced = knowledge_manager.context_enhancer.enhance_context(message)
        
        print(f"Base Context: {json.dumps({k: v for k, v in enhanced.items() if k != 'knowledge'}, indent=2)}")
        print(f"Has Knowledge: {enhanced['knowledge']['has_relevant_knowledge']}")
        
        if enhanced['knowledge']['has_relevant_knowledge']:
            print(f"Knowledge Summary: {enhanced['knowledge']['knowledge_summary']}")
            
            # Test response enhancement
            original_response = "This is a simulated AI response without knowledge enhancement."
            enhanced_response = knowledge_manager.enhance_response_with_knowledge(
                message, original_response, enhanced
            )
            
            print(f"\nEnhanced Response: {enhanced_response['enhanced_response'][:200]}...")
