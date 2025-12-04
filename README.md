# Tariff Optimizer

AI-powered tariff optimization application for international shipping.

## Features

- **Dual Authentication System**: Session-based auth for web UI, HTTP Basic Auth for API endpoints
- **AvaTax API Integration**: Full integration with Avalara AvaTax API (sandbox & production)
- **AI-Powered Analysis**: OpenAI GPT-3.5-turbo for intelligent tariff analysis
- **RAG System**: Knowledge base for legal/customs documentation with context-aware AI responses
- **Learning System**: Accumulates insights from past analyses to improve future recommendations
- **CORS Support**: Cross-origin requests enabled for API integration
- **Automatic Deployment**: CI/CD pipeline via GitHub Actions to Render.com
- **Health Monitoring**: Built-in health check endpoint

## Prerequisites

- Python 3.11+
- pip (Python package installer)
- Git
- GitHub account
- Render.com account

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd TariffOptimizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and go to: `http://localhost:5001`

## Project Structure

```
TariffOptimizer/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render.com configuration
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── README.md                  # This file
├── DEPLOYMENT.md              # Deployment guide
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Actions CI/CD workflow
├── templates/
│   └── index.html             # Main HTML template
└── static/
    └── style.css              # CSS styles
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Flask Secret Key (for session management)
SECRET_KEY=your-random-secret-key-change-this-in-production

# AvaTax API Bearer Token
AVATAX_BEARER_TOKEN=your_avatax_bearer_token_here

# OpenAI API Key (for ChatGPT integration)
OPENAI_API_KEY=your_openai_api_key_here

# Basic Authentication Credentials
AUTH_USER=Admin
AUTH_PASS=your_secure_password_here
```

**Important:**
- Never commit the `.env` file to Git
- Use strong, random values for `SECRET_KEY` and `AUTH_PASS` in production
- Set all these variables in your Render.com dashboard under Environment settings

## API Endpoints

### Web Pages (Session Auth)
- `GET /` - Main landing page (requires login)
- `GET /login` - Login page
- `GET /logout` - Logout and clear session

### API Endpoints (HTTP Basic Auth)
- `GET /health` - Health check endpoint (public)
- `POST /api/verify` - Verify AvaTax transaction with AI analysis
- `POST /api/clear-session` - Clear chat history

### API Usage Example

```bash
# Verify transaction with AI analysis
curl -X POST https://tariff-optimizer2.onrender.com/api/verify \
  -u Admin:Secret_6681940 \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "sandbox",
    "bearerToken": "your_avatax_token",
    "issueDescription": "Verify duty calculation for electronics",
    "userRequest": {
      "companyCode": "DEFAULT",
      "type": "SalesOrder",
      "date": "2025-12-04",
      "addresses": {
        "ShipFrom": {"country": "CN"},
        "ShipTo": {"country": "US"}
      },
      "lines": [{
        "amount": 1000,
        "hsCode": "8517.62.00"
      }]
    }
  }'
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Render.com.

## Technologies Used

- **Backend**: Flask (Python)
- **Server**: Gunicorn
- **Deployment**: Render.com
- **CI/CD**: GitHub Actions
- **AI Integration**: OpenAI API (ready to integrate)

## Next Steps

1. Implement your tariff optimization logic in `app.py`
2. Add API endpoints for your specific use cases
3. Integrate ChatGPT API for agentic enhancements
4. Build RAG system for legal/customs documentation
5. Customize the frontend in `templates/index.html`
6. Add tests in a `tests/` directory
7. Update documentation as you build features

## Development Tips

- Use `logger.debug()`, `logger.info()`, `logger.error()` for logging
- Keep sensitive data in `.env` file (never commit it)
- Test locally before pushing to GitHub
- Monitor deployment logs on Render.com dashboard

## Support

For issues or questions, please check the deployment documentation or create an issue in the repository.

## License

[Add your license here]
