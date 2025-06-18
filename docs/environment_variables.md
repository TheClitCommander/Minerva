# Environment Variables in Minerva

This document describes the environment variables used in the Minerva AI system and how they affect the application's behavior.

## Directory Configuration

Minerva uses several environment variables to configure the directories where it stores various types of data. These variables allow you to customize the application's file storage layout without modifying the code.

### Directory Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DOCUMENTS_DIR` | Directory where uploaded documents are stored | `./data/documents` |
| `PROCESSED_DIR` | Directory where processed document data is stored | `./data/processed` |
| `EMBEDDINGS_DIR` | Directory where document embeddings are stored | `./data/embeddings` |

### Usage Examples

#### Local Development

For local development, you can set these variables in your shell before starting the application:

```bash
export DOCUMENTS_DIR="/path/to/custom/documents"
export PROCESSED_DIR="/path/to/custom/processed"
export EMBEDDINGS_DIR="/path/to/custom/embeddings"
python -m web.app
```

#### In Docker

If running Minerva in Docker, you can set these variables in your Docker Compose file:

```yaml
services:
  minerva:
    image: minerva:latest
    environment:
      - DOCUMENTS_DIR=/app/data/documents
      - PROCESSED_DIR=/app/data/processed
      - EMBEDDINGS_DIR=/app/data/embeddings
    volumes:
      - ./data:/app/data
```

#### In Production

For production deployments, you should set these variables in your environment configuration:

```bash
# On Linux/macOS
export DOCUMENTS_DIR="/var/minerva/documents"
export PROCESSED_DIR="/var/minerva/processed"
export EMBEDDINGS_DIR="/var/minerva/embeddings"

# On Windows
set DOCUMENTS_DIR=C:\minerva\documents
set PROCESSED_DIR=C:\minerva\processed
set EMBEDDINGS_DIR=C:\minerva\embeddings
```

## Directory Creation Behavior

If the specified directories do not exist when Minerva starts, they will be created automatically. This makes it easy to deploy Minerva in new environments without manual directory setup.

## Relative Paths

You can use relative paths in these environment variables. Minerva will resolve them relative to the current working directory when the application starts.

Example:
```bash
export DOCUMENTS_DIR="./custom_documents"
export PROCESSED_DIR="./custom_processed"
export EMBEDDINGS_DIR="./custom_embeddings"
```

## Best Practices

1. **Persistence**: Ensure these directories are backed by persistent storage in production environments.
2. **Permissions**: Make sure the application has read/write permissions to these directories.
3. **Backup**: Regularly back up these directories, especially the documents and processed directories.
4. **Standardization**: In a team environment, document the expected directory structure to ensure consistency.

## Troubleshooting

If you encounter issues with file paths or document processing:

1. Verify that the environment variables are set correctly
2. Check that the directories exist and have the correct permissions
3. Look for path-related errors in the application logs
4. For Docker deployments, ensure that the volume mappings are correct

## Additional Configuration

For more advanced configuration options, including memory management and plugin settings, see the `config.py` file and the full documentation.
