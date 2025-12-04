from flask import Flask, render_template, request, jsonify
import os
import logging
from dotenv import load_dotenv

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add your API keys here
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Add other API keys as needed


@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')


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
