#!/usr/bin/env python3
"""
Minerva Command Line Interface

This module provides a command-line interface for interacting with Minerva.
"""

import os
import sys
import json
import click
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from loguru import logger

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Minerva components
from integrations.framework_manager import FrameworkManager

# Set up rich console
console = Console()

# Set up logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("minerva_logs/cli.log", rotation="10 MB", level="DEBUG")

# Initialize the framework manager
framework_manager = FrameworkManager()

@click.group()
def cli():
    """Minerva - Your personal AI assistant."""
    pass

@cli.command()
def list():
    """List all available AI frameworks and their capabilities."""
    frameworks = framework_manager.get_all_frameworks()
    capabilities = framework_manager.get_all_capabilities()
    
    if not frameworks:
        console.print("[bold red]No frameworks loaded![/] Please register some frameworks first.")
        return
    
    # Display frameworks
    console.print("\n[bold blue]================ Available Frameworks ================\n[/]")
    
    for name, info in frameworks.items():
        console.print(f"[bold]* {name}[/]")
        console.print(f"  Path: {info['path']}")
        console.print(f"  Capabilities: {', '.join(info['capabilities'])}")
        console.print("")
    
    # Display capabilities
    console.print("\n[bold blue]================ Available Capabilities ================\n[/]")
    
    for capability, framework_list in capabilities.items():
        console.print(f"[bold]* {capability}[/]")
        console.print(f"  Provided by: {', '.join(framework_list)}")
        console.print("")

@cli.command()
@click.argument("search_path")
def discover(search_path):
    """Discover AI frameworks in the specified directory."""
    # Convert to absolute path if needed
    if not os.path.isabs(search_path):
        search_path = os.path.abspath(search_path)
    
    console.print(f"[bold blue]Discovering frameworks in:[/] {search_path}")
    
    discovered = framework_manager.discover_frameworks(search_path)
    
    if not discovered:
        console.print("[yellow]No frameworks discovered in the specified directory.[/]")
        return
    
    console.print(f"\n[bold green]Discovered {len(discovered)} potential framework(s):[/]")
    
    table = Table(show_header=True)
    table.add_column("Name")
    table.add_column("Path")
    table.add_column("Status")
    
    for framework in discovered:
        name = framework['name']
        path = framework['path']
        
        # Check if already registered
        info = framework_manager.get_framework_info(name)
        status = "[green]Already registered[/]" if info else "[yellow]Not registered[/]"
        
        table.add_row(name, path, status)
    
    console.print(table)
    console.print("\nUse [bold]minerva register <name> <path>[/] to register a framework.")

@cli.command()
@click.argument("name")
@click.argument("path", required=False)
def register(name, path=None):
    """Register an AI framework with Minerva."""
    if path is None and name:
        # If only one argument provided, assume it's a path and derive name
        path = os.path.abspath(name)
        name = os.path.basename(path)
    else:
        # Convert to absolute path if needed
        if path and not os.path.isabs(path):
            path = os.path.abspath(path)
    
    console.print(f"[bold blue]Registering framework:[/] {name} at {path}")
    
    success = framework_manager.register_framework(name, path)
    
    if success:
        console.print(f"[bold green]Successfully registered framework:[/] {name}")
        
        # Show capabilities
        info = framework_manager.get_framework_info(name)
        if info:
            console.print(f"Capabilities: {', '.join(info['capabilities'])}")
    else:
        console.print(f"[bold red]Failed to register framework:[/] {name}")

@cli.command()
@click.argument("name")
def info(name):
    """Get detailed information about a specific framework."""
    info = framework_manager.get_framework_info(name)
    
    if not info:
        console.print(f"[bold red]Framework not found:[/] {name}")
        return
    
    # Display framework info
    panel = Panel(
        f"[bold]Name:[/] {info['name']}\n"
        f"[bold]Path:[/] {info['path']}\n"
        f"[bold]Version:[/] {info['version']}\n"
        f"[bold]Description:[/] {info['description']}\n"
        f"[bold]Capabilities:[/] {', '.join(info['capabilities'])}",
        title=f"Framework Information: {info['name']}",
        border_style="blue"
    )
    
    console.print(panel)

@cli.command()
@click.option("--prompt", "-p", required=True, help="Code generation prompt")
@click.option("--framework", "-f", help="Framework to use for code generation")
@click.option("--context", "-c", help="Additional context for code generation")
@click.option("--output", "-o", help="File to write the generated code to")
def generate(prompt, framework=None, context=None, output=None):
    """Generate code using an AI framework."""
    console.print(f"[bold blue]Generating code for prompt:[/] {prompt}")
    
    try:
        if framework:
            console.print(f"Using framework: {framework}")
            result = framework_manager.execute_with_framework(
                framework, "generate_code", prompt, context
            )
        else:
            console.print("Finding best framework for code generation...")
            result = framework_manager.execute_with_capability(
                "code_generation", "generate_code", prompt, context
            )
            
        # Get the framework name that was used
        used_framework = framework or framework_manager.get_best_framework_for_capability("code_generation")
        
        # Display the generated code
        console.print(f"\n[bold blue]================ Generated Code ({used_framework}) ================\n[/]")
        
        if "code" in result:
            # Format and display the code
            code = result["code"]
            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Save to file if requested
            if output:
                with open(output, "w") as f:
                    f.write(code)
                console.print(f"\n[green]Code saved to:[/] {output}")
        
        # Display any notes
        if "note" in result:
            console.print(f"\n[yellow]Note:[/] {result['note']}")
            
    except Exception as e:
        console.print(f"[bold red]Error generating code:[/] {str(e)}")

@cli.command()
@click.option("--task", "-t", required=True, help="Task to execute")
@click.option("--framework", "-f", help="Framework to use for execution")
@click.option("--context", "-c", help="Context file (JSON) for task execution")
def execute(task, framework=None, context=None):
    """Execute a task using an AI framework."""
    console.print(f"[bold blue]Executing task:[/] {task}")
    
    # Load context if provided
    context_data = None
    if context:
        try:
            with open(context, "r") as f:
                context_data = json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load context file:[/] {str(e)}")
    
    try:
        if framework:
            console.print(f"Using framework: {framework}")
            result = framework_manager.execute_with_framework(
                framework, "execute_task", task, context_data
            )
        else:
            console.print("Finding best framework for task execution...")
            result = framework_manager.execute_with_capability(
                "task_execution", "execute_task", task, context_data
            )
            
        # Get the framework name that was used
        used_framework = framework or framework_manager.get_best_framework_for_capability("task_execution")
        
        # Display the execution result
        console.print(f"\n[bold blue]================ Task Execution ({used_framework}) ================\n[/]")
        
        console.print(f"Task: {task}\n")
        
        if "result" in result:
            console.print(f"Result:")
            console.print(result["result"])
            
        if "status" in result:
            status_color = "green" if result["status"] == "completed" else "yellow"
            console.print(f"\nStatus: [bold {status_color}]{result['status']}[/]")
        
        # Display any notes
        if "note" in result:
            console.print(f"\n[yellow]Note:[/] {result['note']}")
            
    except Exception as e:
        console.print(f"[bold red]Error executing task:[/] {str(e)}")

@cli.command()
@click.argument("name")
def unregister(name):
    """Unregister a framework from Minerva."""
    console.print(f"[bold yellow]Unregistering framework:[/] {name}")
    
    success = framework_manager.unregister_framework(name)
    
    if success:
        console.print(f"[bold green]Successfully unregistered framework:[/] {name}")
    else:
        console.print(f"[bold red]Failed to unregister framework:[/] {name}")

@cli.command()
@click.option("--capability", "-c", required=True, help="Capability to rate")
@click.option("--framework", "-f", required=True, help="Framework to rate")
@click.option("--score", "-s", required=True, type=float, help="Score (0-100)")
def rate(capability, framework, score):
    """Rate a framework's capability."""
    console.print(f"[bold blue]Rating capability:[/] {capability} for {framework} with score {score}")
    
    framework_manager.update_capability_score(capability, framework, score)
    
    console.print(f"[bold green]Successfully updated rating.[/]")

@cli.command()
def list_frameworks():
    """List all available AI frameworks."""
    frameworks = framework_manager.get_all_frameworks()
    
    click.echo(click.style("\n=== Available AI Frameworks ===", fg="green", bold=True))
    
    if not frameworks:
        click.echo(click.style("No frameworks available", fg="yellow"))
        return
    
    for name, info in frameworks.items():
        click.echo(click.style(f"\n{name}", fg="blue", bold=True))
        if isinstance(info, dict):
            if 'capabilities' in info:
                capabilities = ", ".join(info['capabilities'])
                click.echo(f"Capabilities: {capabilities}")
        else:
            # Handle the case where info is a BaseIntegration instance
            capabilities = ", ".join(info.capabilities)
            click.echo(f"Capabilities: {capabilities}")
            if hasattr(info, 'version'):
                click.echo(f"Version: {info.version}")
            if hasattr(info, 'description'):
                click.echo(f"Description: {info.description}")

@cli.command()
def list_capabilities():
    """List all available capabilities and the frameworks that provide them."""
    capabilities = framework_manager.get_all_capabilities()
    
    click.echo(click.style("\n=== Available Capabilities ===", fg="green", bold=True))
    
    if not capabilities:
        click.echo(click.style("No capabilities available", fg="yellow"))
        return
    
    for capability, frameworks in capabilities.items():
        click.echo(click.style(f"\n{capability}", fg="blue", bold=True))
        frameworks_str = ", ".join(frameworks)
        click.echo(f"Provided by: {frameworks_str}")

@cli.group()
def memory():
    """Memory management commands."""
    pass

@memory.command()
@click.option('--content', '-c', required=True, help='Content of the memory')
@click.option('--category', '-t', required=True, help='Category of the memory (e.g., preference, fact)')
@click.option('--importance', '-i', type=int, default=5, help='Importance (1-10)')
@click.option('--tag', '-g', multiple=True, help='Tags for the memory')
def add(content, category, importance, tag):
    """Add a new memory."""
    minerva = initialize_minerva()
    
    result = minerva.add_memory(
        content=content,
        category=category,
        importance=importance,
        tags=list(tag) if tag else None
    )
    
    if result['status'] == 'success':
        click.echo(click.style(f"Memory added successfully with ID: {result['id']}", fg="green"))
    else:
        click.echo(click.style(f"Error adding memory: {result.get('message', 'Unknown error')}", fg="red"))

@memory.command()
@click.option('--query', '-q', help='Text to search for')
@click.option('--category', '-c', help='Category to filter by')
@click.option('--tag', '-t', multiple=True, help='Tags to filter by')
@click.option('--max-results', '-m', type=int, default=5, help='Maximum number of results')
def search(query, category, tag, max_results):
    """Search for memories."""
    minerva = initialize_minerva()
    
    result = minerva.search_memories(
        query=query,
        category=category,
        tags=list(tag) if tag else None,
        max_results=max_results
    )
    
    if result['status'] == 'success':
        click.echo(click.style(f"\nFound {result['count']} memories:", fg="green"))
        
        for memory in result['memories']:
            click.echo(click.style(f"\nID: {memory['id']}", fg="blue"))
            click.echo(f"Content: {memory['content']}")
            click.echo(f"Category: {memory['category']}")
            click.echo(f"Importance: {memory['importance']}")
            tags_str = ", ".join(memory['tags']) if memory['tags'] else "None"
            click.echo(f"Tags: {tags_str}")
            click.echo(f"Created: {memory['created_at']}")
    else:
        click.echo(click.style(f"Error searching memories: {result.get('message', 'Unknown error')}", fg="red"))

@cli.group()
def conversation():
    """Conversation management commands."""
    pass

@conversation.command()
@click.option('--user-id', '-u', default="default_user", help='User ID')
def start(user_id):
    """Start a new conversation."""
    minerva = initialize_minerva()
    
    result = minerva.start_conversation(user_id=user_id)
    
    if result['status'] == 'success':
        click.echo(click.style(f"Conversation started with ID: {result['conversation_id']}", fg="green"))
        click.echo(f"User ID: {result['user_id']}")
    else:
        click.echo(click.style(f"Error starting conversation: {result.get('message', 'Unknown error')}", fg="red"))

@conversation.command()
@click.option('--conversation-id', '-c', required=True, help='Conversation ID')
@click.option('--role', '-r', required=True, help='Role (user or assistant)')
@click.option('--content', '-m', required=True, help='Message content')
def add_message(conversation_id, role, content):
    """Add a message to a conversation."""
    minerva = initialize_minerva()
    
    result = minerva.add_message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    
    if result['status'] == 'success':
        click.echo(click.style(f"Message added to conversation {conversation_id}", fg="green"))
    else:
        click.echo(click.style(f"Error adding message: {result.get('message', 'Unknown error')}", fg="red"))

if __name__ == "__main__":
    cli()
