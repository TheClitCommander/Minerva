"""
Enhanced Memory Manager for Minerva

This module provides an improved memory system with:
- SQLite-based persistent storage (replacing JSON)
- Hash-based deduplication to prevent duplicate memories
- Enhanced metadata tagging with categories, timestamps, and usage metrics
- Query expansion for better memory retrieval
- Context-aware memory ranking and prioritization
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the base memory manager for compatibility
from memory.memory_manager import MemoryItem


class EnhancedMemoryManager:
    """
    Enhanced memory manager with SQLite storage, hash-based deduplication,
    and improved memory retrieval capabilities.
    
    Features:
    - SQLite-based persistent storage (replacing JSON files)
    - Hash-based memory deduplication
    - Enhanced metadata and tracking (access count, timestamps)
    - Query expansion for better memory matching
    - Context-aware memory ranking
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the enhanced memory manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        # Set up database path
        if db_path is None:
            home_dir = str(Path.home())
            storage_dir = os.path.join(home_dir, ".minerva", "memory")
            os.makedirs(storage_dir, exist_ok=True)
            self.db_path = os.path.join(storage_dir, "memories.db")
        else:
            self.db_path = db_path
            
        logger.info(f"Enhanced Memory Manager initialized with database at: {self.db_path}")
        
        # Initialize database connection
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            # Connect to database (will create it if it doesn't exist)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create memories table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                importance INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                expires_at TIMESTAMP
            )
            ''')
            
            # Create tags table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (memory_id, tag),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
            ''')
            
            # Create metadata table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_metadata (
                memory_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (memory_id, key),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
            ''')
            
            # Create context reference table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_contexts (
                memory_id TEXT NOT NULL,
                context_reference TEXT NOT NULL,
                score REAL NOT NULL DEFAULT 1.0,
                PRIMARY KEY (memory_id, context_reference),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
            ''')
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
            
    def _get_connection(self):
        """Get a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for the memory content for deduplication."""
        # Normalize content by removing extra whitespace and converting to lowercase
        normalized_content = ' '.join(content.lower().split())
        return hashlib.md5(normalized_content.encode()).hexdigest()
    
    def add_memory(self, content: str, source: str, category: str, 
                 importance: int = 1, tags: List[str] = None, 
                 context: str = None,
                 expires_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new memory item with deduplication.
        
        Args:
            content: The content of the memory
            source: Where the memory came from (e.g., 'user', 'system', 'inference')
            category: Category of the memory (e.g., 'preference', 'fact', 'instruction')
            importance: Importance score (1-10)
            tags: List of tags for search/retrieval
            context: Optional context reference for context-sensitive memories
            expires_at: When the memory should expire (or None for never)
            metadata: Additional metadata as key-value pairs
            
        Returns:
            The created memory item as a dictionary
        """
        if tags is None:
            tags = []
            
        if metadata is None:
            metadata = {}
        
        # Generate content hash for deduplication
        content_hash = self._generate_content_hash(content)
        
        # Generate unique ID
        memory_id = str(uuid.uuid4())
        
        # Current timestamp
        now = datetime.now()
        
        # Check for existing memories with the same content hash
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Look for existing memory with the same hash
            cursor.execute(
                "SELECT id, access_count FROM memories WHERE content_hash = ?", 
                (content_hash,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Memory already exists - update access count and timestamp
                existing_id = existing['id']
                new_count = existing['access_count'] + 1
                
                cursor.execute(
                    "UPDATE memories SET last_accessed = ?, access_count = ? WHERE id = ?",
                    (now.isoformat(), new_count, existing_id)
                )
                
                conn.commit()
                logger.info(f"Found duplicate memory. Updated access count for {existing_id}")
                
                # Return the existing memory
                return self.get_memory_by_id(existing_id)
            
            # No duplicate found - insert new memory
            expires_str = expires_at.isoformat() if expires_at else None
            
            # Insert the memory record
            cursor.execute('''
            INSERT INTO memories 
            (id, content, content_hash, category, source, importance, 
             created_at, last_accessed, access_count, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (memory_id, content, content_hash, category, source, importance,
                  now.isoformat(), now.isoformat(), 1, expires_str))
            
            # Store tags
            for tag in tags:
                cursor.execute(
                    "INSERT INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                    (memory_id, tag)
                )
            
            # Store metadata
            for key, value in metadata.items():
                # Convert value to string if it's not already
                if not isinstance(value, str):
                    value = json.dumps(value)
                    
                cursor.execute(
                    "INSERT INTO memory_metadata (memory_id, key, value) VALUES (?, ?, ?)",
                    (memory_id, key, value)
                )
            
            # Store context reference if provided
            if context:
                cursor.execute(
                    "INSERT INTO memory_contexts (memory_id, context_reference, score) VALUES (?, ?, ?)",
                    (memory_id, context, 1.0)  # Default score of 1.0
                )
            
            # Commit transaction
            conn.commit()
            logger.info(f"Added new memory: {memory_id} ({category})")
            
            # Return the newly created memory
            return self.get_memory_by_id(memory_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error adding memory: {str(e)}")
            raise
        finally:
            conn.close()
            
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory item by ID.
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            The memory item as a dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get the basic memory record
            cursor.execute(
                "SELECT * FROM memories WHERE id = ?", 
                (memory_id,)
            )
            memory = cursor.fetchone()
            
            if not memory:
                return None
                
            # Convert to dictionary
            memory_dict = dict(memory)
            
            # Update access information
            now = datetime.now()
            new_count = memory_dict['access_count'] + 1
            
            cursor.execute(
                "UPDATE memories SET last_accessed = ?, access_count = ? WHERE id = ?",
                (now.isoformat(), new_count, memory_id)
            )
            
            # Get tags
            cursor.execute(
                "SELECT tag FROM memory_tags WHERE memory_id = ?",
                (memory_id,)
            )
            tags = [row['tag'] for row in cursor.fetchall()]
            memory_dict['tags'] = tags
            
            # Get metadata
            cursor.execute(
                "SELECT key, value FROM memory_metadata WHERE memory_id = ?",
                (memory_id,)
            )
            metadata = {row['key']: row['value'] for row in cursor.fetchall()}
            memory_dict['metadata'] = metadata
            
            # Get context references
            cursor.execute(
                "SELECT context_reference, score FROM memory_contexts WHERE memory_id = ?",
                (memory_id,)
            )
            contexts = {row['context_reference']: row['score'] for row in cursor.fetchall()}
            memory_dict['contexts'] = contexts
            
            # Update the memory access count in the database
            memory_dict['access_count'] = new_count
            
            conn.commit()
            return memory_dict
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
            return None
        finally:
            conn.close()
            
    def _expand_query(self, query: str) -> List[str]:
        """
        Expand a query with synonyms and related terms for better matching.
        
        Args:
            query: The original search query
            
        Returns:
            List of expanded query terms
        """
        # Basic query expansion - split into words and add original query
        expanded = [query.lower()]
        
        # Add individual words
        words = [w.strip() for w in query.lower().split() if len(w.strip()) > 2]
        expanded.extend(words)
        
        # Add simple synonym pairs (this would be enhanced with a proper thesaurus)
        synonyms = {
            'like': ['enjoy', 'love', 'prefer', 'fond of'],
            'dislike': ['hate', 'detest', 'cannot stand', 'not a fan of'],
            'happy': ['joy', 'pleased', 'glad', 'delighted'],
            'sad': ['unhappy', 'depressed', 'disappointed', 'upset'],
            'hobby': ['interest', 'pastime', 'leisure activity', 'passion'],
            'food': ['meal', 'dish', 'cuisine', 'cooking'],
            'movie': ['film', 'cinema', 'show', 'picture'],
            'book': ['novel', 'publication', 'reading', 'literature'],
            'job': ['career', 'profession', 'occupation', 'work'],
            'travel': ['trip', 'journey', 'vacation', 'holiday']
        }
        
        # Add synonyms for words in the query
        for word in words:
            if word in synonyms:
                expanded.extend(synonyms[word])
                
        # Return unique expanded terms
        return list(set(expanded))
    
    def get_memories(self, query: str = None, category: str = None, 
                    tags: List[str] = None, source: str = None,
                    context: str = None,
                    min_importance: int = None, max_results: int = 10,
                    include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        Search for memory items based on criteria with query expansion.
        
        Args:
            query: Text to search for in content
            category: Category to filter by
            tags: Tags to filter by
            source: Source to filter by
            context: Context reference to filter by
            min_importance: Minimum importance score
            max_results: Maximum number of results
            include_expired: Whether to include expired memories
            
        Returns:
            List of matching memory items with relevance scores
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Start building the query
            sql_conditions = []
            sql_params = []
            
            # Apply filters
            if category:
                sql_conditions.append("category = ?")
                sql_params.append(category)
                
            if source:
                sql_conditions.append("source = ?")
                sql_params.append(source)
                
            if min_importance:
                sql_conditions.append("importance >= ?")
                sql_params.append(min_importance)
                
            if not include_expired:
                sql_conditions.append("(expires_at IS NULL OR expires_at > ?)")
                sql_params.append(datetime.now().isoformat())
            
            # Join conditions with AND
            where_clause = ""
            if sql_conditions:
                where_clause = "WHERE " + " AND ".join(sql_conditions)
            
            # Get base results without full-text search
            cursor.execute(f"""
                SELECT id, content, category, source, importance, 
                       created_at, last_accessed, access_count, expires_at 
                FROM memories {where_clause}
                ORDER BY importance DESC, last_accessed DESC
            """, sql_params)
            
            base_results = cursor.fetchall()
            results = [dict(row) for row in base_results]
            
            # Apply text search if query is provided
            if query:
                # Expand query terms
                expanded_terms = self._expand_query(query)
                
                # Score results based on relevance to query terms
                scored_results = []
                for result in results:
                    content = result['content'].lower()
                    score = 0
                    matches = 0
                    
                    # Score based on term matches
                    for term in expanded_terms:
                        if term in content:
                            matches += 1
                            # Original query matches are worth more
                            if term == expanded_terms[0]:  
                                score += 2
                            else:
                                score += 1
                                
                    # Add recency and importance factors
                    last_accessed = datetime.fromisoformat(result['last_accessed'])
                    days_since_access = (datetime.now() - last_accessed).days
                    
                    # Recency boost (inverse of days since access)
                    recency_factor = 1.0 / max(1, days_since_access)
                    
                    # Importance boost
                    importance_factor = result['importance'] / 10.0
                    
                    # Usage frequency boost
                    usage_factor = min(1.0, result['access_count'] / 10.0)
                    
                    # Combined score
                    if matches > 0:
                        final_score = score * (0.5 + 0.3 * recency_factor + 0.1 * importance_factor + 0.1 * usage_factor)
                        result['relevance'] = round(final_score, 2)
                        scored_results.append(result)
                
                # Sort by relevance score
                scored_results.sort(key=lambda x: x['relevance'], reverse=True)
                results = scored_results[:max_results]
            else:
                # No query - enrich results with tags and metadata
                enriched_results = []
                for result in results[:max_results]:
                    memory_id = result['id']
                    complete_memory = self.get_memory_by_id(memory_id)
                    if complete_memory:
                        enriched_results.append(complete_memory)
                results = enriched_results
            
            # Apply tag filtering if specified
            if tags and results:
                filtered_results = []
                for result in results:
                    memory_id = result['id']
                    
                    # Get memory tags
                    cursor.execute(
                        "SELECT tag FROM memory_tags WHERE memory_id = ?",
                        (memory_id,)
                    )
                    memory_tags = [row['tag'] for row in cursor.fetchall()]
                    result['tags'] = memory_tags
                    
                    # Check if all required tags are present
                    if all(tag in memory_tags for tag in tags):
                        filtered_results.append(result)
                        
                results = filtered_results
            
            # Apply context filtering if specified
            if context and results:
                filtered_results = []
                for result in results:
                    memory_id = result['id']
                    
                    # Check for context reference
                    cursor.execute(
                        "SELECT score FROM memory_contexts WHERE memory_id = ? AND context_reference = ?",
                        (memory_id, context)
                    )
                    context_match = cursor.fetchone()
                    
                    if context_match:
                        result['context_score'] = context_match['score']
                        filtered_results.append(result)
                        
                results = filtered_results
            
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
        finally:
            conn.close()
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if memory exists
            cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
            if not cursor.fetchone():
                logger.warning(f"Cannot delete memory {memory_id}: not found")
                return False
                
            # Due to foreign key constraints with ON DELETE CASCADE,
            # deleting from the main memories table will automatically delete
            # related rows in the tags, metadata, and contexts tables
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            # Check if any rows were affected
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Deleted memory: {memory_id}")
                return True
            else:
                conn.rollback()
                return False
                
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            return False
        finally:
            conn.close()
    
    def delete_memories_by_query(self, query: str, category: str = None, exact_match: bool = False) -> int:
        """
        Delete multiple memories matching a query.
        
        Args:
            query: Text to search for in content
            category: Optional category to limit deletion to
            exact_match: If True, only delete exact content matches
            
        Returns:
            Number of memories deleted
        """
        # First get the matching memories
        matches = self.get_memories(query=query, category=category, max_results=100)
        
        if not matches:
            return 0
            
        # If exact_match is True, filter to exact matches only
        if exact_match:
            normalized_query = ' '.join(query.lower().split())
            matches = [m for m in matches if ' '.join(m['content'].lower().split()) == normalized_query]
        
        # Delete each matching memory
        deleted_count = 0
        for memory in matches:
            if self.delete_memory(memory['id']):
                deleted_count += 1
                
        return deleted_count
    
    def update_memory(self, memory_id: str, content: str = None, category: str = None, 
                    importance: int = None, tags: List[str] = None, 
                    expires_at: Optional[datetime] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing memory item.
        
        Args:
            memory_id: ID of the memory to update
            content: New content for the memory (or None to leave unchanged)
            category: New category (or None to leave unchanged)
            importance: New importance score (or None to leave unchanged)
            tags: New tags (or None to leave unchanged)
            expires_at: New expiration date (or None to leave unchanged)
            metadata: New metadata (or None to leave unchanged)
            
        Returns:
            Updated memory item or None if not found/error
        """
        # First check if memory exists
        existing_memory = self.get_memory_by_id(memory_id)
        if not existing_memory:
            logger.warning(f"Cannot update memory {memory_id}: not found")
            return None
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Prepare update fields
            update_fields = []
            update_values = []
            
            # Current timestamp for last_accessed
            now = datetime.now()
            update_fields.append("last_accessed = ?")
            update_values.append(now.isoformat())
            
            # Update content if provided (and generate new hash)
            if content is not None:
                update_fields.append("content = ?")
                update_values.append(content)
                
                # Also update the content hash for deduplication
                new_hash = self._generate_content_hash(content)
                update_fields.append("content_hash = ?")
                update_values.append(new_hash)
            
            # Update other scalar fields if provided
            if category is not None:
                update_fields.append("category = ?")
                update_values.append(category)
                
            if importance is not None:
                # Validate importance range
                if not 1 <= importance <= 10:
                    raise ValueError("Importance must be between 1 and 10")
                    
                update_fields.append("importance = ?")
                update_values.append(importance)
            
            if expires_at is not None:
                update_fields.append("expires_at = ?")
                update_values.append(expires_at.isoformat())
            
            # Apply updates to memories table if there are any field updates
            if update_fields:
                query = f"UPDATE memories SET {', '.join(update_fields)} WHERE id = ?"
                update_values.append(memory_id)
                cursor.execute(query, update_values)
            
            # Update tags if provided
            if tags is not None:
                # Delete existing tags
                cursor.execute("DELETE FROM memory_tags WHERE memory_id = ?", (memory_id,))
                
                # Insert new tags
                for tag in tags:
                    cursor.execute(
                        "INSERT INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                        (memory_id, tag)
                    )
            
            # Update metadata if provided
            if metadata is not None:
                # Strategy: Delete existing and insert new
                cursor.execute("DELETE FROM memory_metadata WHERE memory_id = ?", (memory_id,))
                
                # Insert new metadata key-value pairs
                for key, value in metadata.items():
                    # Convert value to string if it's not already
                    if not isinstance(value, str):
                        value = json.dumps(value)
                        
                    cursor.execute(
                        "INSERT INTO memory_metadata (memory_id, key, value) VALUES (?, ?, ?)",
                        (memory_id, key, value)
                    )
            
            # Commit transaction
            conn.commit()
            logger.info(f"Updated memory: {memory_id}")
            
            # Return the updated memory
            return self.get_memory_by_id(memory_id)
            
        except (sqlite3.Error, ValueError) as e:
            conn.rollback()
            logger.error(f"Error updating memory {memory_id}: {str(e)}")
            return None
        finally:
            conn.close()
