"""
Integration module to add enhanced analytics to Minerva
This should be imported in the main minimal_chat_server.py
"""

def integrate_enhanced_analytics(app):
    """
    Integrate enhanced analytics module with the main Flask application
    
    Args:
        app: The Flask application instance
    """
    try:
        # Import and register enhanced analytics routes
        from enhanced_analytics_routes import register_enhanced_analytics_routes
        register_enhanced_analytics_routes(app)
        
        print("[STARTUP] ✅ Enhanced Analytics module successfully integrated")
        return True
    except Exception as e:
        print(f"[STARTUP] ❌ Failed to integrate Enhanced Analytics module: {str(e)}")
        return False
