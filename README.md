# Tariff Optimizer

AI-powered tariff optimization application for international shipping.

## Features

- Flask-based web application with session-based authentication
- AvaTax API integration for tariff calculations
- OpenAI API integration for AI-powered insights
- User authentication system
- Automatic deployment to Render.com via GitHub Actions
- Health check endpoint for monitoring
- Prepared for RAG system implementation for legal/customs documentation

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

- `GET /` - Main landing page
- `GET /health` - Health check endpoint

Add your custom endpoints in `app.py`.

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
