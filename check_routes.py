#!/usr/bin/env python3
"""
Script to check the registered routes in the Minerva web application.
"""
from web.app import app, init_app

# Initialize the app
init_app()

# Print all registered routes
print("\n=== REGISTERED ROUTES ===")
for rule in app.url_map.iter_rules():
    print(f"Route: {rule}, Endpoint: {rule.endpoint}")
print("========================\n")
