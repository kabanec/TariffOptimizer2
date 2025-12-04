from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import os
import logging
from dotenv import load_dotenv

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Load API keys and credentials
AVATAX_BEARER_TOKEN = os.getenv('AVATAX_BEARER_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AUTH_USER = os.getenv('AUTH_USER', 'Admin')
AUTH_PASS = os.getenv('AUTH_PASS', 'Secret_6681940')


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Basic authentication check
def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASS


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_auth(username, password):
            session['authenticated'] = True
            session['username'] = username
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main landing page - protected by authentication"""
    return render_template('index.html', username=session.get('username'))


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy'}), 200


# Add your API endpoints here
# Example:
# @app.route('/api/optimize', methods=['POST'])
# def optimize_tariff():
#     try:
#         data = request.json
#         # Your tariff optimization logic here
#         return jsonify({'result': 'success'})
#     except Exception as e:
#         logger.error(f"Error: {str(e)}")
#         return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
