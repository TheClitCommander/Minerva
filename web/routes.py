"""
Routes configuration for Minerva web application.

This module explicitly registers all the routes for the Minerva web UI,
ensuring that dashboard, chat, analytics and other UI components are accessible.
"""

def register_ui_routes(app):
    """
    Register all UI routes for Minerva web application.
    
    Args:
        app: Flask application instance
    """
    # Import the view functions directly
    from web.app import index, chat, chat_test, hybrid_chat_test, simple_chat
    from web.app import model_insights, think_tank_insights, memories, knowledge
    from web.app import settings, plugins, direct_test_page
    
    # Main UI routes
    app.add_url_rule('/', view_func=index, methods=['GET'])
    app.add_url_rule('/dashboard', view_func=index, methods=['GET'])
    app.add_url_rule('/chat', view_func=chat, methods=['GET'])
    app.add_url_rule('/chat_test', view_func=chat_test, methods=['GET'])
    app.add_url_rule('/hybrid_chat_test', view_func=hybrid_chat_test, methods=['GET'])
    app.add_url_rule('/simple_chat', view_func=simple_chat, methods=['GET'])
    
    # Analytics and insights routes
    app.add_url_rule('/analytics-dashboard', endpoint='analytics_dashboard', view_func=index, methods=['GET'])
    app.add_url_rule('/enhanced-analytics', endpoint='enhanced_analytics', view_func=index, methods=['GET'])
    app.add_url_rule('/model-insights', view_func=model_insights, methods=['GET'])
    app.add_url_rule('/think-tank-insights', view_func=think_tank_insights, methods=['GET'])
    
    # Memory and knowledge management
    app.add_url_rule('/memories', view_func=memories, methods=['GET'])
    app.add_url_rule('/knowledge', view_func=knowledge, methods=['GET'])
    
    # Settings and configuration
    app.add_url_rule('/settings', view_func=settings, methods=['GET'])
    app.add_url_rule('/plugins', view_func=plugins, methods=['GET'])
    
    # Direct API test
    app.add_url_rule('/direct-test', view_func=direct_test_page, methods=['GET'])
    
    print("[ROUTES] Successfully registered all UI routes")
    return app
