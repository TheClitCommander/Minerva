#!/bin/bash
# Load environment variables
export $(grep -v '^#' /Users/bendickinson/Desktop/Minerva/.env | xargs)

# Start web server
cd /Users/bendickinson/Desktop/Minerva/web
python -m http.server 8080 &
echo "Web server started on port 8080"

# Start API server
python minerva_server.py --port 8888 &
echo "API server started on port 8888"

# Keep script running
echo "Servers are running. Press Ctrl+C to stop."
wait
