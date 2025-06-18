"""
Minerva AI - Knowledge Enhancer Plugin

This plugin enhances the knowledge management system with additional capabilities:
1. Auto-categorization of documents
2. Smart summarization of content
3. Keyword extraction
4. Related document suggestions
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import Counter
from pathlib import Path

# Import the base Plugin class
from plugins.base import Plugin

# Import Minerva components needed for integration
from knowledge.knowledge_manager import KnowledgeManager

logger = logging.getLogger("minerva.plugins.knowledge_enhancer")


class KnowledgeEnhancerPlugin(Plugin):
    """
    Plugin for enhancing knowledge management functionality.
    
    This plugin adds auto-categorization, summarization, keyword extraction,
    and related document suggestions to the knowledge management system.
    """
    
    plugin_id = "knowledge_enhancer"
    plugin_name = "Knowledge Enhancer"
    plugin_version = "1.0.0"
    plugin_description = "Enhances the knowledge management system with auto-categorization, summarization, and more"
    plugin_author = "Minerva Team"
    plugin_tags = ["knowledge", "categorization", "summarization", "enhancement"]
    
    def __init__(self):
        """Initialize the knowledge enhancer plugin."""
        super().__init__()
        self.knowledge_manager = None
        self.document_categories = {}
        self.document_keywords = {}
        self.document_summaries = {}
        self.related_documents = {}
        self.config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "config",
            "knowledge_enhancer_plugin.json"
        )
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Get the KnowledgeManager instance
            from web.app import knowledge_manager
            self.knowledge_manager = knowledge_manager
            
            # Load existing data
            self._load_data()
            
            # Register hooks with the knowledge manager for new documents
            self._register_hooks()
            
            self._is_initialized = True
            logger.info("Knowledge Enhancer plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Enhancer plugin: {e}")
            return False
    
    def _load_data(self) -> None:
        """Load saved categorization and metadata from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.document_categories = data.get("categories", {})
                    self.document_keywords = data.get("keywords", {})
                    self.document_summaries = data.get("summaries", {})
                    self.related_documents = data.get("related_documents", {})
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading Knowledge Enhancer data: {e}")
            # Initialize with empty data
            self.document_categories = {}
            self.document_keywords = {}
            self.document_summaries = {}
            self.related_documents = {}
    
    def _save_data(self) -> bool:
        """
        Save categorization and metadata to file.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump({
                    "categories": self.document_categories,
                    "keywords": self.document_keywords,
                    "summaries": self.document_summaries,
                    "related_documents": self.related_documents
                }, f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Error saving Knowledge Enhancer data: {e}")
            return False
    
    def _register_hooks(self) -> None:
        """Register hooks for document events."""
        # In a real implementation, we would register callbacks for document events
        # For now, we'll manually process documents
        pass
    
    def process_document(self, document_id: str) -> Dict[str, Any]:
        """
        Process a document to extract enhanced metadata.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Dictionary with enhanced metadata
        """
        try:
            # Get document content
            document_info = self.knowledge_manager.get_document(document_id)
            if not document_info:
                logger.error(f"Document not found: {document_id}")
                return {"error": "Document not found"}
            
            # Get document chunks
            chunks = self.knowledge_manager.get_document_chunks(document_id)
            if not chunks:
                logger.error(f"No chunks found for document: {document_id}")
                return {"error": "No document content available"}
            
            # Combine all chunk content
            full_text = " ".join([chunk.get("content", "") for chunk in chunks])
            
            # Process the document
            category = self._categorize_document(full_text)
            keywords = self._extract_keywords(full_text)
            summary = self._generate_summary(full_text)
            
            # Store the results
            self.document_categories[document_id] = category
            self.document_keywords[document_id] = keywords
            self.document_summaries[document_id] = summary
            
            # Find related documents
            related = self._find_related_documents(document_id, keywords)
            self.related_documents[document_id] = related
            
            # Save data
            self._save_data()
            
            # Return the enhanced metadata
            return {
                "document_id": document_id,
                "category": category,
                "keywords": keywords,
                "summary": summary,
                "related_documents": related
            }
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            return {"error": f"Failed to process document: {str(e)}"}
    
    def _categorize_document(self, text: str) -> str:
        """
        Categorize a document based on its content.
        
        This is a simple implementation that categorizes based on keyword frequency.
        A more sophisticated implementation would use machine learning.
        
        Args:
            text: Document text
            
        Returns:
            Category name
        """
        # Define category keywords
        categories = {
            "technical": [
                "code", "algorithm", "function", "class", "method", "api", 
                "database", "server", "programming", "software"
            ],
            "business": [
                "strategy", "marketing", "sales", "customer", "product", 
                "revenue", "market", "client", "profit", "business"
            ],
            "research": [
                "study", "research", "analysis", "experiment", "data", 
                "results", "findings", "methodology", "hypothesis", "conclusion"
            ],
            "legal": [
                "law", "legal", "rights", "regulation", "compliance", 
                "contract", "agreement", "policy", "terms", "liability"
            ],
            "educational": [
                "learning", "education", "training", "course", "student", 
                "teacher", "curriculum", "lesson", "school", "academic"
            ]
        }
        
        # Count category keyword occurrences
        category_scores = {category: 0 for category in categories}
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        for category, keywords in categories.items():
            for keyword in keywords:
                # Count word occurrences (ensuring we match whole words only)
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                category_scores[category] += count
        
        # Get the category with the highest score
        if all(score == 0 for score in category_scores.values()):
            return "uncategorized"
        
        max_category = max(category_scores.items(), key=lambda x: x[1])
        return max_category[0]
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract important keywords from document text.
        
        This is a simple implementation that uses word frequency.
        A more sophisticated implementation would use TF-IDF or NLP techniques.
        
        Args:
            text: Document text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Preprocess text
        text = text.lower()
        # Remove special characters and replace with spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize
        words = text.split()
        
        # Remove common stop words (a very basic list for demonstration)
        stop_words = {
            "a", "an", "the", "and", "or", "but", "if", "then", "of", "in", "on", "at",
            "to", "for", "with", "by", "about", "as", "into", "like", "through", "after",
            "before", "between", "from", "up", "down", "is", "am", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did", "I", "you",
            "he", "she", "it", "we", "they", "this", "that", "these", "those"
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get the most common words
        most_common = word_counts.most_common(max_keywords)
        
        # Return just the keywords
        return [word for word, _ in most_common]
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a summary of the document content.
        
        This is a simple implementation that extracts important sentences.
        A more sophisticated implementation would use NLP techniques.
        
        Args:
            text: Document text
            max_length: Maximum length of the summary
            
        Returns:
            Document summary
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if not sentences:
            return ""
        
        if len(sentences) == 1 or len(text) <= max_length:
            # If there's only one sentence or the text is already short enough
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # For a simple summary, take the first 2 sentences which often contain
        # the main idea of the document in many types of writing
        summary = " ".join(sentences[:2])
        
        # If the summary is still too long, truncate it
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def _find_related_documents(self, document_id: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Find documents related to the given document based on keyword similarity.
        
        Args:
            document_id: ID of the document to find related documents for
            keywords: Keywords of the document
            
        Returns:
            List of related document information
        """
        # Get all document IDs
        all_documents = self.knowledge_manager.list_documents()
        if not all_documents:
            return []
        
        related_docs = []
        keyword_set = set(keywords)
        
        for doc in all_documents:
            other_id = doc.get("id")
            
            # Skip the current document
            if other_id == document_id:
                continue
            
            # Get keywords for the other document
            other_keywords = self.document_keywords.get(other_id, [])
            if not other_keywords:
                # Try to process the document if it hasn't been processed yet
                try:
                    self.process_document(other_id)
                    other_keywords = self.document_keywords.get(other_id, [])
                except:
                    continue
            
            # Calculate similarity score (intersection of keyword sets)
            other_keyword_set = set(other_keywords)
            common_keywords = keyword_set.intersection(other_keyword_set)
            
            if common_keywords:
                similarity_score = len(common_keywords) / max(len(keyword_set), len(other_keyword_set))
                
                # Only include if there's some meaningful similarity
                if similarity_score > 0.1:
                    related_docs.append({
                        "id": other_id,
                        "title": doc.get("title", "Unknown"),
                        "similarity_score": similarity_score,
                        "common_keywords": list(common_keywords)
                    })
        
        # Sort by similarity score (descending)
        related_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top 5 related documents
        return related_docs[:5]
    
    def get_document_enhancement(self, document_id: str) -> Dict[str, Any]:
        """
        Get enhancement information for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dictionary with enhancement information
        """
        # Check if we already have information for this document
        if document_id in self.document_categories:
            return {
                "document_id": document_id,
                "category": self.document_categories.get(document_id, "uncategorized"),
                "keywords": self.document_keywords.get(document_id, []),
                "summary": self.document_summaries.get(document_id, ""),
                "related_documents": self.related_documents.get(document_id, [])
            }
        
        # Process the document if not already processed
        return self.process_document(document_id)
    
    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all documents in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of document information
        """
        documents = []
        
        for doc_id, doc_category in self.document_categories.items():
            if doc_category == category:
                # Get document information from knowledge manager
                doc_info = self.knowledge_manager.get_document(doc_id)
                if doc_info:
                    documents.append({
                        "id": doc_id,
                        "title": doc_info.get("title", "Unknown"),
                        "keywords": self.document_keywords.get(doc_id, []),
                        "summary": self.document_summaries.get(doc_id, "")
                    })
        
        return documents
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the plugin.
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            # Handle any plugin-specific configuration
            # For example, updating category definitions, etc.
            return True
        except Exception as e:
            logger.error(f"Error configuring Knowledge Enhancer plugin: {e}")
            return False
    
    def shutdown(self) -> bool:
        """
        Shut down the plugin.
        
        Returns:
            True if shutdown was successful, False otherwise
        """
        # Save any unsaved data
        self._save_data()
        
        self._is_initialized = False
        logger.info("Knowledge Enhancer plugin shut down")
        return True
