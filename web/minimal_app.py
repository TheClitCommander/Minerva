from flask import Flask, render_template, send_file
import os

# Create a minimal Flask app for testing routes
app = Flask(__name__)
app.secret_key = 'minerva_test_key'
app.debug = True

@app.route('/')
def index():
    """Basic index route for validation"""
    try:
        # First try serving the minerva_central.html directly from web directory
        ui_path = os.path.join(os.path.dirname(__file__), 'minerva_central.html')
        if os.path.exists(ui_path):
            print(f"Found minerva_central.html at {ui_path}")
            return send_file(ui_path)
            
        # If that fails, try index.html from templates
        print("Falling back to index.html template")
        return render_template('index.html')
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        # Return a minimal HTML for debugging
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Minerva Debug</title></head>
        <body>
            <h1>Minerva Route Validation</h1>
            <p>Error: {str(e)}</p>
            <p>Current directory: {os.path.dirname(__file__)}</p>
        </body>
        </html>
        """

@app.route('/dashboard')
def dashboard():
    """Dashboard route for testing navigation"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return f"Dashboard route error: {str(e)}"
        
@app.route('/api/test')
def api_test():
    """Simple API test endpoint"""
    return {"status": "ok", "message": "API is working"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5506, debug=True)
