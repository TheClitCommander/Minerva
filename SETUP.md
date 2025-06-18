# Minerva AI - Setup Guide

This document provides instructions for setting up the Minerva AI environment, including the web interface and knowledge management system.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup Steps

### 1. Create a Virtual Environment

It's recommended to use a virtual environment to keep the dependencies isolated. You can create one using the built-in `venv` module:

```bash
# Navigate to the Minerva project directory
cd /path/to/Minerva

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies

Once your virtual environment is activated, install the required dependencies:

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Optional: Install Document Processing Dependencies

For enhanced document processing capabilities (PDF and DOCX support), install additional packages:

```bash
pip install PyPDF2 python-docx
```

### 4. Optional: Install Embedding Model Dependencies

For semantic search and embedding generation capabilities:

```bash
pip install sentence-transformers
```

## Running the Web Interface

After setting up your environment, you can run the web interface using the provided script:

```bash
# Make sure your virtual environment is activated
# Then run:
python run_web_interface.py
```

This will start the web server at http://127.0.0.1:5000 by default.

For additional options:

```bash
# Show available options
python run_web_interface.py --help

# Run on a different port
python run_web_interface.py --port 8080

# Run on all interfaces (accessible from other devices on the network)
python run_web_interface.py --host 0.0.0.0

# Run in debug mode (for development)
python run_web_interface.py --debug
```

## Using the Knowledge Management System

The Knowledge Management system allows you to:

1. Upload documents (PDF, DOCX, TXT, etc.)
2. Search through your knowledge base
3. Manage document metadata

To use this feature:

1. Navigate to the Knowledge page in the web interface
2. Upload documents using the form on the left
3. Add metadata to your documents for better organization
4. Use the search functionality to find relevant information

## Development Notes

### Project Structure

- `web/` - Web interface components
  - `app.py` - Flask application
  - `templates/` - HTML templates
  - `static/` - CSS, JavaScript, and other static files
- `knowledge/` - Knowledge management system
  - `document_processor.py` - Handles document processing
  - `knowledge_retriever.py` - Retrieves relevant knowledge
  - `knowledge_manager.py` - Manages the knowledge system

### Troubleshooting

If you encounter issues:

1. Check that your virtual environment is activated
2. Verify that all dependencies are installed correctly
3. Look for error messages in the console output
4. Check the logs in the Flask application output

For installation errors with sentence-transformers or document processing libraries, you may need to install additional system dependencies depending on your OS.

## Next Steps

After setting up, you might want to:

1. Add your own documents to the knowledge base
2. Customize the web interface appearance
3. Integrate with additional AI frameworks
4. Extend the memory system with your own implementations

For any issues or contributions, please refer to the project's main README and documentation.
