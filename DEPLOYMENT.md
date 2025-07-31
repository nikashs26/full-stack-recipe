# 🚀 Deployment Guide

This guide will help you deploy your full-stack recipe app to Railway (backend) and Netlify (frontend).

## 📋 Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **Netlify Account** - Sign up at [netlify.com](https://netlify.com)

## 🔧 Step 1: Deploy Backend to Railway

### 1.1 Push Code to GitHub
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### 1.2 Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the Python backend and deploy it

### 1.3 Get Your Railway URL
1. In your Railway dashboard, click on your project
2. Go to the "Settings" tab
3. Copy the "Domain" URL (it will look like `https://your-app-name.railway.app`)

## 🌐 Step 2: Deploy Frontend to Netlify

### 2.1 Connect to GitHub
1. Go to [netlify.com](https://netlify.com)
2. Click "New site from Git"
3. Choose GitHub and select your repository

### 2.2 Configure Build Settings
- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Node version**: `18`

### 2.3 Set Environment Variables
1. In your Netlify dashboard, go to "Site settings" > "Environment variables"
2. Add the following variable:
   - **Key**: `REACT_APP_API_URL`
   - **Value**: `https://your-railway-url.railway.app/api` (replace with your actual Railway URL)

### 2.4 Deploy
1. Click "Deploy site"
2. Netlify will build and deploy your frontend

## 🔍 Step 3: Test Your Deployment

### 3.1 Test Backend
```bash
curl https://your-railway-url.railway.app/api/health
```
Should return: `{"status": "up"}`

### 3.2 Test Frontend
1. Visit your Netlify URL
2. Try generating a meal plan
3. Check that it connects to your Railway backend

## 🛠️ Troubleshooting

### Backend Issues
- **Port issues**: Make sure `app.py` uses `os.environ.get("PORT", 5003)`
- **Dependencies**: Check that `requirements.txt` includes all needed packages
- **Environment variables**: Set any needed env vars in Railway dashboard

### Frontend Issues
- **API URL**: Verify `REACT_APP_API_URL` is set correctly in Netlify
- **CORS**: Backend should allow requests from your Netlify domain
- **Build errors**: Check the build logs in Netlify dashboard

### Common Issues
1. **CORS errors**: Add your Netlify domain to the CORS allowed origins in `backend/app.py`
2. **API not found**: Make sure the Railway URL is correct and includes `/api`
3. **Build failures**: Check that all dependencies are in `package.json`

## 🔧 Environment Variables

### Railway (Backend)
- `PORT`: Automatically set by Railway
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `HUGGINGFACE_API_KEY`: Your Hugging Face API key (if using HF)

### Netlify (Frontend)
- `REACT_APP_API_URL`: Your Railway backend URL (e.g., `https://your-app.railway.app/api`)

## 📊 Monitoring

### Railway
- Check the "Deployments" tab for build logs
- Use the "Metrics" tab to monitor performance
- Check "Logs" for runtime errors

### Netlify
- Check "Deploys" for build status
- Use "Functions" tab if using serverless functions
- Monitor "Analytics" for site performance

## 🎉 Success!

Once deployed, your app will be available at:
- **Frontend**: `https://your-app-name.netlify.app`
- **Backend**: `https://your-app-name.railway.app`

The frontend will automatically connect to your Railway backend for all API calls! 