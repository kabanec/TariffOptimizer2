# Deployment Guide - Tariff Optimizer

This guide walks you through deploying the Tariff Optimizer application to Render.com with automatic CI/CD via GitHub Actions.

## Overview

The application uses GitHub Actions to automatically deploy to Render.com whenever code is pushed to the `master` or `main` branch.

## Prerequisites

1. GitHub account with a repository for this project
2. Render.com account
3. GitHub repository: [Your repository URL]

## Step-by-Step Setup

### Step 1: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `tariff-optimizer` (or your preferred name)
   - **Region**: Oregon (or your preferred region)
   - **Branch**: `main` or `master`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or your preferred plan)
5. Click **"Create Web Service"**
6. **IMPORTANT**: Copy your Service ID from the URL
   - It looks like: `srv-xxxxxxxxxxxxx`
   - You'll need this for GitHub secrets

### Step 2: Get Your Render API Key

1. Go to [Render API Keys](https://dashboard.render.com/account/api-keys)
2. Click **"Create API Key"**
3. Name it: "GitHub Actions Deploy"
4. **Copy the API key** (starts with `rnd_`)
5. Save it securely - you'll need it in the next step

### Step 3: Configure Environment Variables in Render

1. Go to your Render service dashboard
2. Click **"Environment"** tab
3. Add your environment variables:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: [Your OpenAI API key]

   Add other API keys as needed for your application.

4. Click **"Save Changes"**

### Step 4: Add GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add the following secrets:

   **Secret 1:**
   - Name: `RENDER_API_KEY`
   - Value: [Your Render API key from Step 2]

   **Secret 2:**
   - Name: `RENDER_SERVICE_ID`
   - Value: [Your Render Service ID from Step 1, e.g., `srv-xxxxxxxxxxxxx`]

### Step 5: Initialize Git Repository (if not already done)

```bash
cd /Users/test/Avalara/TariffOptimizer
git init
git add .
git commit -m "Initial commit: Tariff Optimizer with CI/CD setup"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 6: Verify Deployment

1. **GitHub Actions**:
   - Go to your repository → **Actions** tab
   - You should see the "Deploy to Render" workflow running
   - Wait for it to complete (green checkmark)

2. **Render Dashboard**:
   - Go to your [Render service dashboard](https://dashboard.render.com/)
   - Click on your "tariff-optimizer" service
   - Check the **Deploys** tab
   - Wait for deployment to complete

3. **Access Your Application**:
   - Once deployed, Render will provide a URL like: `https://tariff-optimizer.onrender.com`
   - Open it in your browser to verify it's working

## How It Works

### Automatic Deployment Flow

1. You push code to `main` or `master` branch
2. GitHub Actions workflow triggers automatically
3. Workflow installs dependencies and runs tests
4. Workflow calls Render API to trigger deployment
5. Render pulls latest code and deploys your app

### Manual Deployment

You can also trigger deployment manually:

1. Go to GitHub repository → **Actions** tab
2. Select **"Deploy to Render"** workflow
3. Click **"Run workflow"** → **"Run workflow"**

## Monitoring and Logs

### GitHub Actions Logs
- Repository → **Actions** tab
- Click on any workflow run to see logs

### Render Logs
- Render Dashboard → Your Service → **Logs** tab
- View real-time application logs

### Health Check
- Visit: `https://your-app.onrender.com/health`
- Should return: `{"status": "healthy"}`

## Configuration Files

### `.github/workflows/deploy.yml`
GitHub Actions workflow that:
- Triggers on push to main/master
- Sets up Python 3.11
- Installs dependencies
- Deploys to Render via API

### `render.yaml`
Render configuration (Infrastructure as Code):
- Defines service type and settings
- Specifies build and start commands
- Lists environment variables

## Troubleshooting

### Deployment Fails

**Check GitHub Actions Logs:**
1. Repository → Actions → Click failed workflow
2. Look for error messages in the logs

**Check Render Logs:**
1. Render Dashboard → Your Service → Logs
2. Look for startup errors

**Common Issues:**
- Missing environment variables in Render
- Incorrect GitHub secrets
- Python version mismatch
- Missing dependencies in `requirements.txt`

### Application Not Starting

1. Verify `gunicorn` is in `requirements.txt`
2. Check environment variables are set in Render
3. Verify Python version is 3.11 in `render.yaml`
4. Check Render logs for specific errors

### API Key Issues

If you see errors about missing API keys:
1. Go to Render Dashboard → Environment
2. Verify all required API keys are set
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Testing Locally Before Deployment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally
python app.py

# Test with gunicorn (production server)
gunicorn app:app

# Visit http://localhost:8000 (gunicorn) or http://localhost:5001 (Flask dev server)
```

## Deployment Checklist

Before deploying, ensure:

- [ ] Code is committed to Git
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] `requirements.txt` is up to date
- [ ] Render service is created
- [ ] Render API key is generated
- [ ] Render Service ID is copied
- [ ] GitHub secrets (`RENDER_API_KEY`, `RENDER_SERVICE_ID`) are set
- [ ] Render environment variables (e.g., `OPENAI_API_KEY`) are set
- [ ] Code works locally
- [ ] Repository is pushed to GitHub

## Updating the Application

To deploy changes:

```bash
# Make your changes to the code
git add .
git commit -m "Description of changes"
git push origin main
```

GitHub Actions will automatically deploy your changes to Render!

## Environment-Specific Configuration

### Development (Local)
- Uses `.env` file
- Flask debug mode enabled
- Runs on port 5001

### Production (Render)
- Uses Render environment variables
- Gunicorn production server
- Automatic HTTPS
- Health checks enabled

## Security Best Practices

- Never commit API keys or secrets to Git
- Use GitHub Secrets for CI/CD credentials
- Use Render environment variables for application secrets
- Keep `.env` in `.gitignore`
- Rotate API keys regularly
- Use HTTPS in production (automatic on Render)

## Next Steps

1. **Add Tests**: Create `tests/` directory and add unit tests
2. **Add Linting**: Add flake8 or pylint to GitHub Actions workflow
3. **Add Staging Environment**: Create a separate Render service for staging
4. **Add Monitoring**: Set up application monitoring and alerts
5. **Add Database**: Configure PostgreSQL on Render if needed
6. **Custom Domain**: Add your custom domain in Render settings

## Support Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Render Documentation](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## Quick Reference

**Render Dashboard**: https://dashboard.render.com/
**GitHub Actions**: [Your-Repo]/actions
**Health Check**: https://your-app.onrender.com/health

---

**Need Help?**
If you encounter issues, check the logs first:
1. GitHub Actions logs for deployment issues
2. Render logs for application runtime issues
3. Local testing to reproduce issues
