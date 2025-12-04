# Tariff Optimizer - Setup Instructions

## Quick Start - Environment Variables for Render

You need to add these environment variables to your Render service:

### Go to Render Dashboard
https://dashboard.render.com/web/srv-d4oti0idbo4c73fsrmog/env

### Add These Environment Variables:

| Variable Name | Value | Notes |
|--------------|-------|-------|
| `SECRET_KEY` | `your-random-secret-key` | Generate a random string (e.g., using `openssl rand -hex 32`) |
| `AVATAX_BEARER_TOKEN` | [Your AvaTax token] | From Avalara dashboard |
| `OPENAI_API_KEY` | [Your OpenAI key] | From OpenAI platform |
| `AUTH_USER` | `Admin` | Username for login |
| `AUTH_PASS` | `Secret_6681940` | Password for login (change in production!) |

### Steps:
1. Click "Add Environment Variable" for each one
2. Enter the Key and Value
3. Click "Save Changes"
4. Render will automatically redeploy

---

## What's Been Implemented

### Authentication System ✅
- Login page at `/login`
- Session-based authentication
- Protected routes with `@login_required` decorator
- Logout functionality at `/logout`
- User welcome message and logout link on main page

### Environment Configuration ✅
- Flask secret key for sessions
- AvaTax API bearer token (ready to use)
- OpenAI API key (ready to use)
- Configurable auth credentials
- All properly documented in README.md

### Application Structure ✅
```
app.py:1-17  - Imports and configuration
app.py:19-23 - Environment variables loaded
app.py:27-38 - Authentication helpers (@login_required, check_auth)
app.py:41-57 - Login route with POST handling
app.py:60-66 - Logout route
app.py:69-73 - Protected index page
app.py:76-79 - Health check endpoint
```

### Templates ✅
- `login.html` - Styled login form
- `index.html` - Updated with user info and logout

---

## Testing Locally

1. **Create `.env` file:**
```bash
cp .env.example .env
```

2. **Edit `.env` with your values:**
```bash
SECRET_KEY=your-random-secret-key
AVATAX_BEARER_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
AUTH_USER=Admin
AUTH_PASS=Secret_6681940
```

3. **Run the app:**
```bash
python app.py
```

4. **Test:**
- Go to: http://localhost:5001
- Should redirect to login
- Login with: `Admin` / `Secret_6681940`
- Should see main page with welcome message

---

## Deployment Status

✅ Code pushed to GitHub
✅ GitHub Actions should trigger automatically
✅ Render will deploy once environment variables are added

**GitHub Actions:** https://github.com/kabanec/TariffOptimizer2/actions
**Render Service:** https://dashboard.render.com/web/srv-d4oti0idbo4c73fsrmog

---

## Next Steps - Building the Application

Now you're ready to add your tariff optimization logic:

### 1. AvaTax Integration
Add endpoints in `app.py` to call AvaTax API using `AVATAX_BEARER_TOKEN`

### 2. OpenAI Integration
Add AI-powered features using `OPENAI_API_KEY`

### 3. Frontend Development
Customize `templates/index.html` with your forms and UI

### 4. RAG System
Build document retrieval system for legal/customs documentation

---

## Important Security Notes

⚠️ **Before going to production:**
1. Generate a strong `SECRET_KEY` using: `openssl rand -hex 32`
2. Change `AUTH_PASS` to a secure password
3. Consider using a proper authentication system (OAuth, JWT, etc.)
4. Enable HTTPS (automatic on Render)
5. Add rate limiting for API endpoints
6. Implement proper logging and monitoring

---

## Helpful Commands

```bash
# Check deployment status
curl https://tariff-optimizer2.onrender.com/health

# View logs locally
python app.py

# Push changes to trigger deployment
git add .
git commit -m "Your changes"
git push origin main

# Check GitHub Actions
open https://github.com/kabanec/TariffOptimizer2/actions
```

---

## Support

- **Repository:** https://github.com/kabanec/TariffOptimizer2
- **Live App:** https://tariff-optimizer2.onrender.com
- **Documentation:** See README.md and DEPLOYMENT.md
