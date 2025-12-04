# API Integration Guide - Tariff Optimizer

## Overview

The Tariff Optimizer now includes full AvaTax API integration with AI-powered analysis using OpenAI GPT-3.5-turbo and a RAG (Retrieval-Augmented Generation) system.

## Architecture

### Dual Authentication System

1. **Session-Based Auth** (Web UI)
   - Login page at `/login`
   - Protects web pages with `@login_required` decorator
   - User-friendly form authentication

2. **HTTP Basic Auth** (API Endpoints)
   - API endpoints protected with `@auth_required` decorator
   - Uses HTTP Basic Authentication header
   - Username/Password from environment variables

### Key Components

```
app.py Structure:
├── Authentication (Lines 60-91)
│   ├── @auth_required - HTTP Basic Auth for APIs
│   └── @login_required - Session auth for web pages
├── Knowledge Base (Lines 94-200)
│   ├── load_kb_file() - Cached KB loading
│   ├── extract_transaction_context() - Extract key data
│   └── build_rag_context() - Build AI context
├── Learning System (Lines 110-129)
│   ├── load_learnings() - Load past insights
│   └── save_learnings() - Save new insights
├── AvaTax Integration (Lines 227-265)
│   └── call_avatax_api() - API calls to sandbox/production
├── AI Analysis (Lines 268-312)
│   ├── get_enhanced_system_prompt() - Build prompt with learnings
│   └── get_ai_analysis() - OpenAI analysis with RAG
└── API Routes (Lines 315-439)
    ├── /login, /logout - Web authentication
    ├── /api/verify - Main transaction verification endpoint
    └── /api/clear-session - Clear chat history
```

## API Endpoint: /api/verify

### Purpose
Verify AvaTax transactions and get AI-powered analysis with tariff insights.

### Authentication
HTTP Basic Auth required:
```
Username: Admin (or AUTH_USER env var)
Password: Secret_6681940 (or AUTH_PASS env var)
```

### Request Format

```json
POST /api/verify
Content-Type: application/json
Authorization: Basic <base64(username:password)>

{
  "environment": "sandbox",  // or "production"
  "bearerToken": "your_avatax_bearer_token",  // Optional if set in env
  "issueDescription": "Brief description of what to analyze",
  "userRequest": {
    // Standard AvaTax CreateTransaction request
    "companyCode": "DEFAULT",
    "type": "SalesOrder",
    "date": "2025-12-04",
    "addresses": {
      "ShipFrom": {
        "country": "CN",
        "line1": "123 Main St",
        "city": "Shanghai"
      },
      "ShipTo": {
        "country": "US",
        "line1": "456 Oak Ave",
        "city": "New York",
        "region": "NY",
        "postalCode": "10001"
      }
    },
    "lines": [
      {
        "amount": 1000,
        "hsCode": "8517.62.00",
        "description": "Smartphones"
      }
    ]
  },
  "userResponse": {
    // Optional: Your expected response for comparison
  }
}
```

### Response Format

```json
{
  "success": true,
  "apiResponse": {
    // Full AvaTax API response
    "totalTax": 150.25,
    "totalAmount": 1150.25,
    "lines": [...],
    "summary": [...]
  },
  "aiAnalysis": "**Root Cause**\nThe duty calculation includes...\n\n**Key Findings**\n- MFN rate: 5%\n- Section 301 tariff: +25%\n...\n\n**Action**\nVerify HS code classification..."
}
```

### Error Responses

```json
// Missing bearer token
{
  "error": "AvaTax bearer token is required"
}

// AvaTax API error
{
  "error": "AvaTax validation error: ...",
  "details": "..."
}

// Authentication failed
HTTP 401 Unauthorized
```

## curl Examples

### Basic Verification

```bash
curl -X POST https://tariff-optimizer2.onrender.com/api/verify \
  -u Admin:Secret_6681940 \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "sandbox",
    "bearerToken": "your_token_here",
    "issueDescription": "Verify duty calculation for electronics import",
    "userRequest": {
      "companyCode": "DEFAULT",
      "type": "SalesOrder",
      "date": "2025-12-04",
      "addresses": {
        "ShipFrom": {"country": "CN"},
        "ShipTo": {"country": "US", "region": "CA", "postalCode": "90210"}
      },
      "lines": [{
        "amount": 5000,
        "hsCode": "8517.62.00",
        "description": "Smartphones"
      }]
    }
  }'
```

### With Expected Response Comparison

```bash
curl -X POST https://tariff-optimizer2.onrender.com/api/verify \
  -u Admin:Secret_6681940 \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "sandbox",
    "issueDescription": "Compare expected vs actual duty",
    "userRequest": { ... },
    "userResponse": {
      "totalTax": 1000,
      "totalAmount": 6000
    }
  }'
```

### Health Check (No Auth Required)

```bash
curl https://tariff-optimizer2.onrender.com/health
# Response: {"status":"healthy"}
```

## Knowledge Base System

### Directory Structure

```
knowledge_base/
├── README.md
├── de_minimis_values.json         # De minimis thresholds by country
├── executive_orders.json          # Executive orders (301, 232, etc.)
├── duty_rules.json                # Incoterms, calculation rules
├── tariff_ranges.json             # HS code chapter ranges
└── recent_tariff_updates.json     # 2025 updates, IEEPA tariffs
```

### How RAG Works

1. **Transaction Analysis**: Extract origin, destination, HS codes, amounts
2. **Context Building**: Load relevant KB files based on transaction
3. **AI Enhancement**: Add KB context to AI prompt
4. **Smart Response**: AI provides context-aware analysis

### Example KB File

```json
{
  "countries": {
    "US": {
      "threshold": 800,
      "currency": "USD",
      "notes": "Section 321 de minimis"
    },
    "GB": {
      "threshold": 135,
      "currency": "GBP"
    }
  }
}
```

## Learning System

### How It Works

1. Each analysis extracts a key learning point
2. Learnings stored in `learnings.json` (max 30)
3. Recent learnings added to AI system prompt
4. Future analyses benefit from past insights

### Example Learning

```json
{
  "timestamp": "2025-12-04T18:30:00",
  "issue_type": "Verify duty calculation for electronics import",
  "learning": "Section 301 tariffs stack on top of MFN rates for Chinese electronics"
}
```

## Environment Variables Required

```bash
# Flask
SECRET_KEY=your-random-secret-key

# AvaTax
AVATAX_BEARER_TOKEN=your_avatax_token

# OpenAI
OPENAI_API_KEY=your_openai_key

# Authentication
AUTH_USER=Admin
AUTH_PASS=Secret_6681940
```

## Testing Locally

### 1. Install Dependencies

```bash
cd /Users/test/Avalara/TariffOptimizer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 3. Run Application

```bash
python app.py
# Runs on http://localhost:5001
```

### 4. Test API Endpoint

```bash
curl -X POST http://localhost:5001/api/verify \
  -u Admin:Secret_6681940 \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "sandbox",
    "issueDescription": "Test transaction",
    "userRequest": {
      "companyCode": "DEFAULT",
      "type": "SalesOrder",
      "date": "2025-12-04",
      "addresses": {
        "ShipFrom": {"country": "CN"},
        "ShipTo": {"country": "US"}
      },
      "lines": [{"amount": 100}]
    }
  }'
```

## Production Deployment

### Render.com Environment Variables

Add these in Render dashboard:

1. `SECRET_KEY` - Generate with `openssl rand -hex 32`
2. `AVATAX_BEARER_TOKEN` - Your AvaTax token
3. `OPENAI_API_KEY` - Your OpenAI API key
4. `AUTH_USER` - API username
5. `AUTH_PASS` - API password

### Deployment Flow

1. Push to GitHub → GitHub Actions triggers
2. Render pulls latest code
3. Installs dependencies from `requirements.txt`
4. Starts with `gunicorn app:app`
5. Health check at `/health`

## Security Considerations

### For Production:

1. **Use Strong Credentials**
   ```bash
   openssl rand -hex 32  # For SECRET_KEY
   ```

2. **HTTPS Only**: Render provides automatic HTTPS

3. **Rate Limiting**: Consider adding rate limiting middleware

4. **API Key Rotation**: Rotate AvaTax and OpenAI keys regularly

5. **Logging**: Monitor authentication failures

6. **CORS**: Currently open - restrict in production:
   ```python
   CORS(app, origins=["https://yourdomain.com"])
   ```

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check AUTH_USER and AUTH_PASS match environment variables
- Verify Basic Auth header is correctly formatted

**AvaTax API Error**
- Verify AVATAX_BEARER_TOKEN is correct
- Check environment (sandbox vs production)
- Validate transaction request format

**OpenAI Error**
- Verify OPENAI_API_KEY is set
- Check API quota/billing

**Knowledge Base Not Loading**
- Create `knowledge_base/` directory
- Add JSON files with proper format
- Check file permissions

## Next Steps

1. **Add Knowledge Base Files**: Populate `knowledge_base/` directory
2. **Customize AI Prompts**: Modify `get_enhanced_system_prompt()`
3. **Add More Endpoints**: Extend API functionality
4. **Build Frontend**: Create UI for transaction verification
5. **Add Tests**: Unit tests for API endpoints
6. **Monitoring**: Add logging and alerts

## Support

- **Repository**: https://github.com/kabanec/TariffOptimizer2
- **Live API**: https://tariff-optimizer2.onrender.com
- **Health Check**: https://tariff-optimizer2.onrender.com/health
