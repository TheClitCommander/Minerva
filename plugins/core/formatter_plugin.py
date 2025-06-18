"""
Minerva AI - Text Formatter Plugin

This plugin provides enhanced text formatting capabilities.
"""

import re
import logging
import markdown
from typing import Dict, Any, List

# Import the base Plugin class
from plugins.base import Plugin

logger = logging.getLogger("minerva.plugins.formatter")


class FormatterPlugin(Plugin):
    """Plugin for advanced text formatting."""
    
    plugin_id = "formatter"
    plugin_name = "Text Formatter"
    plugin_version = "1.0.0"
    plugin_description = "Provides enhanced text formatting capabilities to Minerva"
    plugin_author = "Minerva Team"
    plugin_tags = ["formatting", "markdown", "text", "utility"]
    
    def __init__(self):
        """Initialize the formatter plugin."""
        super().__init__()
        self.markdown_extensions = [
            'extra',  # Tables, footnotes, etc.
            'codehilite',  # Code highlighting
            'smarty',  # Smart quotes, etc.
            'nl2br',  # Newlines to <br>
        ]
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Verify that markdown extensions work
            test_result = markdown.markdown(
                "# Test\n\nTest **bold** and *italic*", 
                extensions=self.markdown_extensions
            )
            if not test_result or "<h1>Test</h1>" not in test_result:
                logger.warning("Markdown conversion test failed")
                return False
                
            self._is_initialized = True
            logger.info("Formatter plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize formatter plugin: {e}")
            return False
    
    def markdown_to_html(self, text: str) -> str:
        """
        Convert Markdown text to HTML.
        
        Args:
            text: The Markdown text to convert
            
        Returns:
            The HTML representation of the Markdown text
        """
        try:
            return markdown.markdown(text, extensions=self.markdown_extensions)
        except Exception as e:
            logger.error(f"Error converting Markdown to HTML: {e}")
            return f"<p>Error converting Markdown: {e}</p>"
    
    def highlight_code(self, code: str, language: str = "") -> str:
        """
        Highlight code syntax.
        
        Args:
            code: The code to highlight
            language: The programming language of the code
            
        Returns:
            HTML with highlighted code
        """
        try:
            # Format as a code block with specified language
            markdown_code = f"```{language}\n{code}\n```"
            return markdown.markdown(
                markdown_code, 
                extensions=['codehilite']
            )
        except Exception as e:
            logger.error(f"Error highlighting code: {e}")
            return f"<pre><code>{code}</code></pre>"
    
    def format_table(self, headers: List[str], rows: List[List[Any]]) -> str:
        """
        Format data as an HTML table.
        
        Args:
            headers: List of column headers
            rows: List of rows, each containing a list of cell values
            
        Returns:
            HTML table representation of the data
        """
        try:
            # Create markdown table
            markdown_table = "| " + " | ".join(headers) + " |\n"
            markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            
            for row in rows:
                # Ensure each row has the same number of columns as headers
                cells = [str(cell) for cell in row[:len(headers)]]
                if len(cells) < len(headers):
                    cells.extend([""] * (len(headers) - len(cells)))
                
                markdown_table += "| " + " | ".join(cells) + " |\n"
            
            return markdown.markdown(
                markdown_table, 
                extensions=['tables']
            )
        except Exception as e:
            logger.error(f"Error formatting table: {e}")
            # Fallback to basic HTML table
            html = "<table><thead><tr>"
            for header in headers:
                html += f"<th>{header}</th>"
            html += "</tr></thead><tbody>"
            
            for row in rows:
                html += "<tr>"
                for i, cell in enumerate(row):
                    if i < len(headers):
                        html += f"<td>{cell}</td>"
                html += "</tr>"
            
            html += "</tbody></table>"
            return html
    
    def sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML content to remove potentially harmful content.
        
        Args:
            html: The HTML content to sanitize
            
        Returns:
            Sanitized HTML content
        """
        try:
            # Simple sanitization - strip script tags and on* attributes
            # For production use, a proper HTML sanitizer library would be better
            html = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL)
            html = re.sub(r"<\s*script.*?>", "", html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r"\son\w+\s*=\s*['\"][^'\"]*['\"]", "", html, flags=re.IGNORECASE)
            
            return html
        except Exception as e:
            logger.error(f"Error sanitizing HTML: {e}")
            return f"<p>Error sanitizing content: {e}</p>"
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize text to a specified maximum length.
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summarized text
        """
        if len(text) <= max_length:
            return text
        
        # Find the last complete sentence that fits
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary = ""
        
        for sentence in sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence + " "
            else:
                break
        
        # If no complete sentence fits, truncate with ellipsis
        if not summary:
            summary = text[:max_length-3] + "..."
        elif summary and len(summary.strip()) < max_length:
            summary = summary.strip()
        else:
            summary = summary.strip() + "..."
        
        return summary
    
    def shutdown(self) -> bool:
        """
        Shut down the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        self._is_initialized = False
        logger.info("Formatter plugin shut down")
        return True
