"""
Migration Script for Enhanced Memory System

This script helps migrate from the original MemoryManager to the new EnhancedMemoryManager.
It transfers all existing memories to the new SQLite-based system while preserving metadata.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import memory managers
try:
    from memory.memory_manager import MemoryManager
    from memory.enhanced_memory_manager import EnhancedMemoryManager
except ImportError as e:
    logger.error(f"Error importing memory managers: {str(e)}")
    logger.error("Make sure all dependencies are installed")
    sys.exit(1)


def migrate_memories():
    """
    Migrate all memories from the original MemoryManager to the EnhancedMemoryManager.
    """
    logger.info("Starting memory migration...")
    
    # Initialize both memory managers
    original_manager = MemoryManager()
    enhanced_manager = EnhancedMemoryManager()
    
    # Load all memories from the original manager
    logger.info("Loading memories from original manager...")
    original_manager.load_all_memories()
    
    # Get all memory items
    memory_items = original_manager.memory_items
    logger.info(f"Found {len(memory_items)} memories to migrate")
    
    # Migrate each memory
    migrated_count = 0
    already_exists_count = 0
    error_count = 0
    
    for memory_id, memory_item in memory_items.items():
        try:
            # Convert MemoryItem to dict
            memory_dict = memory_item.to_dict()
            
            # Extract fields needed for add_memory
            content = memory_dict['content']
            source = memory_dict['source']
            category = memory_dict['category']
            importance = memory_dict['importance']
            tags = memory_dict['tags']
            metadata = memory_dict['metadata']
            
            # Convert ISO datetime strings back to datetime objects if needed
            expires_at = memory_dict.get('expires_at')
            if expires_at and isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            
            # Add to enhanced memory manager
            new_memory = enhanced_manager.add_memory(
                content=content,
                source=source,
                category=category,
                importance=importance,
                tags=tags,
                expires_at=expires_at,
                metadata=metadata
            )
            
            # Check if this was a new memory or if deduplication prevented insertion
            if new_memory['id'] != memory_id:
                already_exists_count += 1
                logger.debug(f"Memory {memory_id} already exists (deduplication)")
            else:
                migrated_count += 1
                
            # Add access count history (approximate)
            if memory_dict['access_count'] > 1:
                for _ in range(memory_dict['access_count'] - 1):
                    enhanced_manager.get_memory_by_id(new_memory['id'])
                    
        except Exception as e:
            logger.error(f"Error migrating memory {memory_id}: {str(e)}")
            error_count += 1
    
    logger.info(f"Migration complete:")
    logger.info(f"  - {migrated_count} memories migrated successfully")
    logger.info(f"  - {already_exists_count} memories already existed (deduplication)")
    logger.info(f"  - {error_count} errors occurred")
    
    return {
        "total": len(memory_items),
        "migrated": migrated_count,
        "duplicates": already_exists_count,
        "errors": error_count
    }


def main():
    """
    Main function to run the migration.
    """
    try:
        result = migrate_memories()
        print("\nMigration Summary:")
        print(f"  Total memories: {result['total']}")
        print(f"  Successfully migrated: {result['migrated']}")
        print(f"  Deduplicated: {result['duplicates']}")
        print(f"  Errors: {result['errors']}")
        print("\nMigration complete!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print(f"\nMigration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
