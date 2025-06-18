#!/usr/bin/env python3
"""
Unified Memory Manager for Minerva

This is the main memory management system that consolidates the best features
from all existing memory managers: JSON-based storage, SQLite persistence,
deduplication, priority ranking, and conversation handling.
"""

import os
import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

from .memory_models import MemoryItem, ConversationMemory, ConversationMessage
from .priority_system import MemoryPriority


class UnifiedMemoryManager:
    """
    Unified memory manager combining features from all previous implementations:
    - SQLite storage for performance and reliability
    - Hash-based deduplication
    - Priority-based ranking and cleanup
    - Conversation tracking
    - Context-aware retrieval
    """
    
    def __init__(self, storage_dir: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the unified memory manager.
        
        Args:
            storage_dir: Directory for memory storage (default: ~/.minerva/memory)
            config: Configuration dictionary for priority system
        """
        # Set up storage directory
        if storage_dir is None:
            home_dir = str(Path.home())
            self.storage_dir = Path(home_dir) / ".minerva" / "memory"
        else:
            self.storage_dir = Path(storage_dir)
        
        # Create directories
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Database path
        self.db_path = self.storage_dir / "unified_memory.db"
        
        # Initialize priority system
        self.priority_system = MemoryPriority(config)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._initialize_database()
        
        # Performance caches
        self._memory_cache = {}
        self._conversation_cache = {}
        
        self.logger.info(f"Unified Memory Manager initialized at: {self.storage_dir}")
    
    def _initialize_database(self):
        """Initialize SQLite database with all required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Memories table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                importance INTEGER NOT NULL CHECK (importance BETWEEN 1 AND 10),
                category TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                expires_at TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                contexts TEXT DEFAULT '{}'
            )
            ''')
            
            # Memory tags table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (memory_id, tag),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
            ''')
            
            # Conversations table  
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                summary TEXT,
                context TEXT DEFAULT '{}',
                start_time TIMESTAMP NOT NULL,
                last_updated TIMESTAMP NOT NULL
            )
            ''')
            
            # Messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_db_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_db_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_last_accessed ON memories(last_accessed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_db_id)')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()
    
    def _get_connection(self):
        """Get database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication."""
        normalized = ' '.join(content.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    # Memory Management Methods
    
    def add_memory(self, content: str, source: str, category: str,
                  importance: Optional[int] = None, tags: Optional[List[str]] = None,
                  context: Optional[str] = None, expires_at: Optional[datetime] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """
        Add a new memory with automatic deduplication and importance suggestion.
        
        Args:
            content: Memory content
            source: Source of the memory
            category: Memory category
            importance: Importance level (1-10, auto-suggested if None)
            tags: List of tags
            context: Context reference
            expires_at: Expiration datetime
            metadata: Additional metadata
            
        Returns:
            Created or existing MemoryItem
        """
        # Auto-suggest importance if not provided
        if importance is None:
            importance = self.priority_system.suggest_memory_importance(content, source, category)
        
        # Default values
        tags = tags or []
        metadata = metadata or {}
        contexts = {context: 1.0} if context else {}
        
        # Generate content hash for deduplication
        content_hash = self._generate_content_hash(content)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check for existing memory with same hash
            cursor.execute("SELECT id FROM memories WHERE content_hash = ?", (content_hash,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing memory
                memory_id = existing['id']
                cursor.execute('''
                UPDATE memories 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE id = ?
                ''', (datetime.now().isoformat(), memory_id))
                
                conn.commit()
                self.logger.info(f"Found duplicate memory, updated: {memory_id}")
                return self.get_memory(memory_id)
            
            # Create new memory
            memory = MemoryItem(
                content=content,
                source=source,
                category=category,
                importance=importance,
                tags=tags,
                expires_at=expires_at,
                metadata=metadata,
                contexts=contexts
            )
            
            # Insert into database
            cursor.execute('''
            INSERT INTO memories 
            (id, content, content_hash, source, importance, category, 
             created_at, last_accessed, access_count, expires_at, metadata, contexts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.id, memory.content, content_hash, memory.source, 
                memory.importance, memory.category, memory.created_at.isoformat(),
                memory.last_accessed.isoformat(), memory.access_count,
                memory.expires_at.isoformat() if memory.expires_at else None,
                json.dumps(memory.metadata), json.dumps(memory.contexts)
            ))
            
            # Insert tags
            for tag in memory.tags:
                cursor.execute(
                    "INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                    (memory.id, tag)
                )
            
            conn.commit()
            
            # Cache the memory
            self._memory_cache[memory.id] = memory
            
            self.logger.info(f"Added new memory: {memory.id} ({category})")
            return memory
            
        except sqlite3.Error as e:
            conn.rollback()
            self.logger.error(f"Error adding memory: {e}")
            raise
        finally:
            conn.close()
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get memory by ID with access tracking."""
        # Check cache first
        if memory_id in self._memory_cache:
            memory = self._memory_cache[memory_id]
            memory.update_access()
            self._update_memory_access(memory_id)
            return memory
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Create memory object
            memory_data = dict(row)
            memory_data['metadata'] = json.loads(memory_data['metadata'] or '{}')
            memory_data['contexts'] = json.loads(memory_data['contexts'] or '{}')
            
            # Parse dates
            for date_field in ['created_at', 'last_accessed', 'expires_at']:
                if memory_data[date_field]:
                    memory_data[date_field] = datetime.fromisoformat(memory_data[date_field])
            
            # Get tags
            cursor.execute("SELECT tag FROM memory_tags WHERE memory_id = ?", (memory_id,))
            memory_data['tags'] = [row['tag'] for row in cursor.fetchall()]
            
            # Remove hash field (not part of MemoryItem model)
            memory_data.pop('content_hash', None)
            
            memory = MemoryItem(**memory_data)
            
            # Update access
            memory.update_access()
            self._update_memory_access(memory_id)
            
            # Cache memory
            self._memory_cache[memory_id] = memory
            
            return memory
            
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None
        finally:
            conn.close()
    
    def _update_memory_access(self, memory_id: str):
        """Update memory access count and timestamp in database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE memories 
            SET last_accessed = ?, access_count = access_count + 1
            WHERE id = ?
            ''', (datetime.now().isoformat(), memory_id))
            conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error updating memory access: {e}")
        finally:
            conn.close()
    
    def search_memories(self, query: Optional[str] = None, category: Optional[str] = None,
                       tags: Optional[List[str]] = None, source: Optional[str] = None,
                       min_importance: Optional[int] = None, max_results: int = 10,
                       include_expired: bool = False,
                       current_context: Optional[str] = None) -> List[Tuple[MemoryItem, float]]:
        """
        Search memories with priority ranking.
        
        Returns:
            List of (memory, priority_score) tuples, sorted by relevance
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Build query
            conditions = []
            params = []
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if source:
                conditions.append("source = ?")
                params.append(source)
            
            if min_importance:
                conditions.append("importance >= ?")
                params.append(min_importance)
            
            if not include_expired:
                conditions.append("(expires_at IS NULL OR expires_at > ?)")
                params.append(datetime.now().isoformat())
            
            # Text search
            if query:
                conditions.append("content LIKE ?")
                params.append(f"%{query}%")
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            cursor.execute(f"SELECT * FROM memories {where_clause}", params)
            rows = cursor.fetchall()
            
            # Convert to memory objects
            memories = []
            for row in rows:
                memory_data = dict(row)
                memory_data['metadata'] = json.loads(memory_data['metadata'] or '{}')
                memory_data['contexts'] = json.loads(memory_data['contexts'] or '{}')
                
                # Parse dates
                for date_field in ['created_at', 'last_accessed', 'expires_at']:
                    if memory_data[date_field]:
                        memory_data[date_field] = datetime.fromisoformat(memory_data[date_field])
                
                # Get tags
                cursor.execute("SELECT tag FROM memory_tags WHERE memory_id = ?", (memory_data['id'],))
                memory_data['tags'] = [tag_row['tag'] for tag_row in cursor.fetchall()]
                
                # Remove hash field
                memory_data.pop('content_hash', None)
                
                memory = MemoryItem(**memory_data)
                memories.append(memory)
            
            # Apply tag filtering
            if tags:
                memories = [m for m in memories if all(tag in m.tags for tag in tags)]
            
            # Rank by priority
            ranked_memories = self.priority_system.rank_memories(
                memories, current_context, max_results
            )
            
            return ranked_memories
            
        except sqlite3.Error as e:
            self.logger.error(f"Error searching memories: {e}")
            return []
        finally:
            conn.close()
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            
            # Remove from cache
            self._memory_cache.pop(memory_id, None)
            
            if deleted:
                self.logger.info(f"Deleted memory: {memory_id}")
            return deleted
            
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting memory: {e}")
            return False
        finally:
            conn.close()
    
    # Conversation Management Methods
    
    def create_conversation(self, user_id: str) -> ConversationMemory:
        """Create a new conversation."""
        conversation = ConversationMemory(user_id=user_id)
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO conversations 
            (id, user_id, conversation_id, summary, context, start_time, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                conversation.id, conversation.user_id, conversation.conversation_id,
                conversation.summary, json.dumps(conversation.context),
                conversation.start_time.isoformat(), conversation.last_updated.isoformat()
            ))
            conn.commit()
            
            # Cache conversation
            self._conversation_cache[conversation.id] = conversation
            
            self.logger.info(f"Created conversation: {conversation.id}")
            return conversation
            
        except sqlite3.Error as e:
            self.logger.error(f"Error creating conversation: {e}")
            raise
        finally:
            conn.close()
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """Get conversation by ID."""
        # Check cache first
        if conversation_id in self._conversation_cache:
            return self._conversation_cache[conversation_id]
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Create conversation object
            conv_data = dict(row)
            conv_data['context'] = json.loads(conv_data['context'] or '{}')
            conv_data['start_time'] = datetime.fromisoformat(conv_data['start_time'])
            conv_data['last_updated'] = datetime.fromisoformat(conv_data['last_updated'])
            
            # Get messages
            cursor.execute('''
            SELECT * FROM messages WHERE conversation_db_id = ? ORDER BY timestamp
            ''', (conversation_id,))
            
            messages = []
            for msg_row in cursor.fetchall():
                msg_data = dict(msg_row)
                msg_data['timestamp'] = datetime.fromisoformat(msg_data['timestamp'])
                msg_data['metadata'] = json.loads(msg_data['metadata'] or '{}')
                msg_data.pop('conversation_db_id')  # Remove foreign key field
                
                message = ConversationMessage(**msg_data)
                messages.append(message)
            
            conv_data['messages'] = messages
            conversation = ConversationMemory(**conv_data)
            
            # Cache conversation
            self._conversation_cache[conversation_id] = conversation
            
            return conversation
            
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving conversation: {e}")
            return None
        finally:
            conn.close()
    
    def add_message_to_conversation(self, conversation_id: str, role: str, content: str,
                                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add message to conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Add message to conversation object
        conversation.add_message(role, content, metadata)
        
        # Get the new message
        new_message = conversation.messages[-1]
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Insert message
            cursor.execute('''
            INSERT INTO messages (id, conversation_db_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                new_message.id, conversation_id, new_message.role, new_message.content,
                new_message.timestamp.isoformat(), json.dumps(new_message.metadata)
            ))
            
            # Update conversation last_updated
            cursor.execute('''
            UPDATE conversations SET last_updated = ? WHERE id = ?
            ''', (conversation.last_updated.isoformat(), conversation_id))
            
            conn.commit()
            
            # Update cache
            self._conversation_cache[conversation_id] = conversation
            
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error adding message to conversation: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_conversations(self, user_id: Optional[str] = None, 
                               max_results: int = 10) -> List[ConversationMemory]:
        """Get recent conversations."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                SELECT id FROM conversations WHERE user_id = ? 
                ORDER BY last_updated DESC LIMIT ?
                ''', (user_id, max_results))
            else:
                cursor.execute('''
                SELECT id FROM conversations ORDER BY last_updated DESC LIMIT ?
                ''', (max_results,))
            
            conversation_ids = [row['id'] for row in cursor.fetchall()]
            
            # Get full conversation objects
            conversations = []
            for conv_id in conversation_ids:
                conversation = self.get_conversation(conv_id)
                if conversation:
                    conversations.append(conversation)
            
            return conversations
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting recent conversations: {e}")
            return []
        finally:
            conn.close()
    
    # Utility Methods
    
    def cleanup_expired_memories(self) -> int:
        """Remove expired memories and return count deleted."""
        candidates = self.priority_system.identify_candidates_for_cleanup(
            list(self._memory_cache.values())
        )
        
        deleted_count = 0
        for memory in candidates:
            if self.delete_memory(memory.id):
                deleted_count += 1
        
        self.logger.info(f"Cleaned up {deleted_count} expired memories")
        return deleted_count
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) as total FROM memories")
            total_memories = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM conversations")
            total_conversations = cursor.fetchone()['total']
            
            # Category distribution
            cursor.execute('''
            SELECT category, COUNT(*) as count FROM memories GROUP BY category
            ''')
            categories = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Get all memories for priority analysis
            cursor.execute("SELECT * FROM memories")
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory_data = dict(row)
                memory_data['metadata'] = json.loads(memory_data['metadata'] or '{}')
                memory_data['contexts'] = json.loads(memory_data['contexts'] or '{}')
                
                for date_field in ['created_at', 'last_accessed', 'expires_at']:
                    if memory_data[date_field]:
                        memory_data[date_field] = datetime.fromisoformat(memory_data[date_field])
                
                memory_data['tags'] = []  # Simplified for stats
                memory_data.pop('content_hash', None)
                
                memory = MemoryItem(**memory_data)
                memories.append(memory)
            
            # Get priority statistics
            priority_stats = self.priority_system.get_memory_statistics(memories)
            
            return {
                'total_memories': total_memories,
                'total_conversations': total_conversations,
                'categories': categories,
                'priority_analysis': priority_stats,
                'storage_path': str(self.storage_dir),
                'database_size_mb': round(self.db_path.stat().st_size / (1024*1024), 2)
            }
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}
        finally:
            conn.close()


# Export the unified manager
__all__ = ['UnifiedMemoryManager'] 