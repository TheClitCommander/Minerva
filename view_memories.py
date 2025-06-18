#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
View Prioritized Memories

A utility script to view project memories by priority, category, or tags.
"""

import argparse
from memory_priority_system import (
    MemoryPrioritySystem,
    PriorityLevel,
    MemoryCategory
)

def format_memory(memory, show_full=False):
    """Format a memory for display."""
    priority_stars = "★" * memory.priority.value
    
    header = f"{priority_stars} {memory.title} {priority_stars}"
    print(f"\n{header}")
    print("=" * len(header))
    print(f"Priority: {memory.priority.name} ({memory.priority.value}/5)")
    print(f"Category: {memory.category.name}")
    print(f"Tags: {', '.join(memory.tags)}")
    print("-" * len(header))
    
    if show_full:
        print(memory.content)
    else:
        # Show first 200 chars with ellipsis if longer
        content_preview = memory.content[:200]
        if len(memory.content) > 200:
            content_preview += "..."
        print(content_preview)
    
    print("-" * len(header))

def main():
    parser = argparse.ArgumentParser(description="View prioritized project memories")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--priority", "-p", 
        type=str,
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "5", "4", "3", "2", "1"],
        help="Filter by minimum priority level"
    )
    group.add_argument(
        "--category", "-c", 
        type=str,
        help="Filter by category"
    )
    group.add_argument(
        "--tags", "-t", 
        type=str,
        help="Filter by tags (comma-separated)"
    )
    parser.add_argument(
        "--all", "-a", 
        action="store_true",
        help="Show all memories"
    )
    parser.add_argument(
        "--full", "-f", 
        action="store_true",
        help="Show full memory content (not just preview)"
    )
    parser.add_argument(
        "--summary", "-s", 
        action="store_true",
        help="Show only summary statistics"
    )
    
    args = parser.parse_args()
    
    # Initialize memory system
    memory_system = MemoryPrioritySystem()
    
    # Handle summary-only view
    if args.summary:
        memory_system.print_summary()
        return
    
    # Get memories based on filters
    if args.priority:
        # Convert string to PriorityLevel
        if args.priority.isdigit():
            priority = PriorityLevel(int(args.priority))
        else:
            priority = PriorityLevel[args.priority]
        
        memories = memory_system.get_memories_by_priority(priority)
        print(f"\nMemories with priority {priority.name} ({priority.value}) or higher:")
    
    elif args.category:
        # Find the matching category
        category = None
        for cat in MemoryCategory:
            if cat.name.lower() == args.category.lower() or cat.value.lower() == args.category.lower():
                category = cat
                break
        
        if category:
            memories = memory_system.get_memories_by_category(category)
            print(f"\nMemories in category {category.name}:")
        else:
            print(f"Error: Category '{args.category}' not found.")
            print(f"Available categories: {', '.join([c.name for c in MemoryCategory])}")
            return
    
    elif args.tags:
        tags = [tag.strip() for tag in args.tags.split(',')]
        memories = memory_system.get_memories_by_tags(tags)
        print(f"\nMemories with tags: {', '.join(tags)}")
    
    elif args.all:
        # Get all memories sorted by priority
        memories = memory_system.get_memories_by_priority(PriorityLevel.INFO)
        print("\nAll memories (sorted by priority):")
    
    else:
        # Default to CRITICAL priority if no filter specified
        memories = memory_system.get_memories_by_priority(PriorityLevel.CRITICAL)
        print("\nCRITICAL priority memories:")
    
    # Display the found memories
    if not memories:
        print("No memories found matching the criteria.")
        return
    
    print(f"Found {len(memories)} memories.")
    
    for memory in memories:
        format_memory(memory, show_full=args.full)
    
    print(f"\nTotal: {len(memories)} memories")

if __name__ == "__main__":
    main()
