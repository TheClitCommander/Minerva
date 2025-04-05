#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conversation Database Module

This module provides persistent storage for Minerva's conversations using SQLite.
It includes schema definitions, CRUD operations, and migration utilities from the
existing JSON-based storage to maintain backward compatibility.
"""

import os
import json
import time
import sqlite3
import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("conversation_db")

# Path constants
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DB_DIR, 'conversations.db')
JSON_MEMORY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'conversation_memory.json')

# Ensure data directory exists
os.makedirs(DB_DIR, exist_ok=True)

class ConversationDB:
    """SQLite database for persistent conversation storage"""
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize the database connection and schema"""
        self.db_path = db_path
        self._initialize_db()
        self._migrate_from_json()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory for dict results"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _initialize_db(self) -> None:
        """Create the database schema if it doesn't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
        ''')
        
        # Create metadata table for extensibility
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metadata_conversation_id ON conversation_metadata(conversation_id)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _migrate_from_json(self) -> None:
        """Migrate existing JSON-based conversation memory to SQLite"""
        if not os.path.exists(JSON_MEMORY_PATH):
            logger.info(f"No JSON memory file found at {JSON_MEMORY_PATH}, skipping migration")
            return
        
        try:
            # Load conversations from JSON
            with open(JSON_MEMORY_PATH, 'r') as f:
                json_conversations = json.load(f)
                
            if not json_conversations:
                logger.info("No conversations found in JSON file, skipping migration")
                return
                
            # Get list of existing conversation IDs to avoid duplicates
            existing_ids = self.get_conversation_ids()
            
            # Track migration statistics
            migrated_count = 0
            skipped_count = 0
            
            # Begin transaction for faster inserts
            conn = self._get_connection()
            conn.execute("BEGIN TRANSACTION")
            
            # Migrate each conversation
            for conv_id, messages in json_conversations.items():
                if conv_id in existing_ids:
                    skipped_count += 1
                    continue
                
                # Generate a title if we have messages
                title = f"Conversation from {datetime.datetime.now().strftime('%Y-%m-%d')}"
                if messages and len(messages) > 0:
                    # Use first user message as title basis
                    for msg in messages:
                        if msg.get('role') == 'user':
                            title_base = msg.get('content', '').strip()
                            if title_base:
                                # Truncate and clean title
                                title = (title_base[:40] + '...') if len(title_base) > 40 else title_base
                                break
                
                # Insert conversation
                created_at = datetime.datetime.now().isoformat()
                if messages and len(messages) > 0 and 'timestamp' in messages[0]:
                    try:
                        created_at = datetime.datetime.fromtimestamp(messages[0]['timestamp']).isoformat()
                    except (KeyError, ValueError, TypeError):
                        pass
                        
                self._insert_conversation(conn, conv_id, title, created_at)
                
                # Insert messages
                for msg in messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    
                    # Try to get timestamp or use current time
                    timestamp = datetime.datetime.now().isoformat()
                    if 'timestamp' in msg:
                        try:
                            timestamp = datetime.datetime.fromtimestamp(msg['timestamp']).isoformat()
                        except (ValueError, TypeError):
                            pass
                    
                    self._insert_message(conn, conv_id, role, content, timestamp)
                
                migrated_count += 1
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            logger.info(f"Migration complete: {migrated_count} conversations migrated, {skipped_count} skipped")
            
            # Create backup of JSON file
            if migrated_count > 0:
                backup_path = f"{JSON_MEMORY_PATH}.bak.{int(time.time())}"
                os.rename(JSON_MEMORY_PATH, backup_path)
                logger.info(f"Created backup of JSON memory file at {backup_path}")
                
        except Exception as e:
            logger.error(f"Error migrating from JSON: {str(e)}")
    
    def _insert_conversation(self, conn, conv_id: str, title: str, created_at: str = None) -> None:
        """Insert a new conversation record"""
        cursor = conn.cursor()
        if created_at:
            cursor.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title, created_at, datetime.datetime.now().isoformat())
            )
        else:
            cursor.execute(
                "INSERT INTO conversations (id, title) VALUES (?, ?)",
                (conv_id, title)
            )
    
    def _insert_message(self, conn, conv_id: str, role: str, content: str, timestamp: str = None) -> None:
        """Insert a message into the database"""
        cursor = conn.cursor()
        if timestamp:
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (conv_id, role, content, timestamp)
            )
        else:
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conv_id, role, content)
            )
    
    def _update_conversation_timestamp(self, conn, conv_id: str) -> None:
        """Update the last_updated timestamp for a conversation"""
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.datetime.now().isoformat(), conv_id)
        )
    
    def create_conversation(self, conv_id: str, title: str = None) -> str:
        """Create a new conversation and return its ID"""
        if not title:
            title = f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        conn = self._get_connection()
        try:
            self._insert_conversation(conn, conv_id, title)
            conn.commit()
            logger.info(f"Created new conversation: {conv_id}")
            return conv_id
        except sqlite3.IntegrityError:
            # Conversation already exists
            conn.rollback()
            logger.warning(f"Conversation already exists: {conv_id}")
            return conv_id
        finally:
            conn.close()
    
    def add_message(self, conv_id: str, role: str, content: str) -> int:
        """Add a message to a conversation and return the message ID"""
        # Ensure conversation exists
        self.create_conversation(conv_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Insert message
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conv_id, role, content)
            )
            message_id = cursor.lastrowid
            
            # Update conversation timestamp
            self._update_conversation_timestamp(conn, conv_id)
            
            conn.commit()
            return message_id
        finally:
            conn.close()
    
    def get_conversation(self, conv_id: str) -> Dict[str, Any]:
        """Get a conversation by ID with its messages"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get conversation details
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        conversation = dict(cursor.fetchone() or {})
        
        if not conversation:
            conn.close()
            return None
        
        # Get messages
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", 
            (conv_id,)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conversation['messages'] = messages
        
        # Get metadata
        cursor.execute(
            "SELECT key, value FROM conversation_metadata WHERE conversation_id = ?",
            (conv_id,)
        )
        metadata = {row['key']: row['value'] for row in cursor.fetchall()}
        conversation['metadata'] = metadata
        
        conn.close()
        return conversation
    
    def get_conversation_messages(self, conv_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get messages for a conversation, optionally limited to the most recent ones"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if limit:
            cursor.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?", 
                (conv_id, limit)
            )
            messages = [dict(row) for row in cursor.fetchall()]
            # Reverse to get oldest first
            messages.reverse()
        else:
            cursor.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", 
                (conv_id,)
            )
            messages = [dict(row) for row in cursor.fetchall()]
            
        conn.close()
        return messages
    
    def get_conversations(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get a list of conversations with their titles and timestamps"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT c.*, COUNT(m.id) as message_count 
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.is_active = 1
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return conversations
    
    def get_conversation_ids(self) -> List[str]:
        """Get a list of all conversation IDs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM conversations")
        ids = [row['id'] for row in cursor.fetchall()]
        
        conn.close()
        return ids
    
    def update_conversation_title(self, conv_id: str, title: str) -> bool:
        """Update the title of a conversation"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conv_id)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_conversation(self, conv_id: str) -> bool:
        """Soft delete a conversation by marking it inactive"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE conversations SET is_active = 0 WHERE id = ?",
            (conv_id,)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def permanently_delete_conversation(self, conv_id: str) -> bool:
        """Permanently delete a conversation and all its messages"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM conversation_metadata WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def export_conversations_to_json(self, output_path: str = None) -> str:
        """Export all conversations to a JSON file for backup or compatibility"""
        if not output_path:
            output_path = os.path.join(DB_DIR, f"conversation_export_{int(time.time())}.json")
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all active conversations
        cursor.execute("SELECT id FROM conversations WHERE is_active = 1")
        conv_ids = [row['id'] for row in cursor.fetchall()]
        
        # Build export data structure (matching original JSON format)
        export_data = {}
        
        for conv_id in conv_ids:
            cursor.execute(
                "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conv_id,)
            )
            messages = []
            for row in cursor.fetchall():
                message = {
                    'role': row['role'],
                    'content': row['content']
                }
                # Add timestamp if available
                if row['timestamp']:
                    try:
                        # Convert ISO timestamp to Unix timestamp for compatibility
                        dt = datetime.datetime.fromisoformat(row['timestamp'])
                        message['timestamp'] = dt.timestamp()
                    except (ValueError, TypeError):
                        pass
                        
                messages.append(message)
                
            export_data[conv_id] = messages
            
        conn.close()
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Exported {len(export_data)} conversations to {output_path}")
        return output_path
    
    def add_metadata(self, conv_id: str, key: str, value: str) -> bool:
        """Add or update metadata for a conversation"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if the key already exists
        cursor.execute(
            "SELECT id FROM conversation_metadata WHERE conversation_id = ? AND key = ?",
            (conv_id, key)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute(
                "UPDATE conversation_metadata SET value = ? WHERE conversation_id = ? AND key = ?",
                (value, conv_id, key)
            )
        else:
            # Insert new
            cursor.execute(
                "INSERT INTO conversation_metadata (conversation_id, key, value) VALUES (?, ?, ?)",
                (conv_id, key, value)
            )
            
        conn.commit()
        conn.close()
        return True
    
    def get_metadata(self, conv_id: str, key: str = None) -> Union[str, Dict[str, str]]:
        """Get metadata for a conversation, optionally filtered by key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if key:
            cursor.execute(
                "SELECT value FROM conversation_metadata WHERE conversation_id = ? AND key = ?",
                (conv_id, key)
            )
            row = cursor.fetchone()
            conn.close()
            return row['value'] if row else None
        else:
            cursor.execute(
                "SELECT key, value FROM conversation_metadata WHERE conversation_id = ?",
                (conv_id,)
            )
            metadata = {row['key']: row['value'] for row in cursor.fetchall()}
            conn.close()
            return metadata
            
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for conversations by content or title"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create full-text search pattern
        search_pattern = f"%{query}%"
        
        # Search in message content and conversation titles
        cursor.execute(
            """
            SELECT DISTINCT c.*, 
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE (c.title LIKE ? OR m.content LIKE ?)
              AND c.is_active = 1
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (search_pattern, search_pattern, limit)
        )
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_conversation_summary(self, conv_id: str) -> Dict[str, Any]:
        """Get a summary of a conversation with message counts by role"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get conversation details
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        conversation = dict(cursor.fetchone() or {})
        
        if not conversation:
            conn.close()
            return None
            
        # Get message counts by role
        cursor.execute(
            """
            SELECT role, COUNT(*) as count
            FROM messages
            WHERE conversation_id = ?
            GROUP BY role
            """,
            (conv_id,)
        )
        
        role_counts = {row['role']: row['count'] for row in cursor.fetchall()}
        conversation['message_counts'] = role_counts
        
        # Get total message count
        cursor.execute(
            "SELECT COUNT(*) as total FROM messages WHERE conversation_id = ?",
            (conv_id,)
        )
        conversation['total_messages'] = cursor.fetchone()['total']
        
        # Get first and last message timestamps
        cursor.execute(
            "SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM messages WHERE conversation_id = ?",
            (conv_id,)
        )
        timestamp_row = cursor.fetchone()
        conversation['first_message'] = timestamp_row['first']
        conversation['last_message'] = timestamp_row['last']
        
        conn.close()
        return conversation


# Create a singleton instance
_db_instance = None

def get_db() -> ConversationDB:
    """Get the singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = ConversationDB()
    return _db_instance

# Export functions for direct usage
def add_message(conv_id: str, role: str, content: str) -> int:
    """Add a message to a conversation and return the message ID"""
    return get_db().add_message(conv_id, role, content)

def get_conversation(conv_id: str) -> Dict[str, Any]:
    """Get a conversation by ID with its messages"""
    return get_db().get_conversation(conv_id)

def get_conversations(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """Get a list of conversations with their titles and timestamps"""
    return get_db().get_conversations(limit, offset)

def create_conversation(conv_id: str, title: str = None) -> str:
    """Create a new conversation and return its ID"""
    return get_db().create_conversation(conv_id, title)
