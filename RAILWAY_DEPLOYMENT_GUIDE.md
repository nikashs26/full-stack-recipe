# Railway + Netlify Deployment Guide

## 🚀 Free Deployment Setup

This guide will help you deploy your full-stack recipe app completely free using Railway (backend) and Netlify (frontend).

## 📋 Prerequisites

- GitHub account
- Railway account (free tier)
- Netlify account (free tier)
- Your recipe app code

## 🔧 Backend Deployment (Railway)

### 1. Railway Setup

1. Go to [Railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `full-stack-recipe` repository
4. Choose the `backend` directory as the source

### 2. Railway Configuration

1. **Build Settings:**
   - Builder: `Dockerfile`
   - Dockerfile Path: `backend/Dockerfile`
   - Source Directory: `backend`

2. **Environment Variables:**
   Add these in Railway dashboard:
   ```
   FLASK_SECRET_KEY=your-super-secret-key-here
   DEBUG=false
   ```

3. **Deploy Settings:**
   - Region: `us-west2` (or closest to you)
   - Restart Policy: `on failure`
   - Max Retries: `10`

### 3. Deploy

1. Click "Deploy" and wait for build to complete
2. Copy your Railway URL (e.g., `https://your-app-name-production.up.railway.app`)

## 🌐 Frontend Deployment (Netlify)

### 1. Netlify Setup

1. Go to [Netlify.com](https://netlify.com) and sign in with GitHub
2. Click "New site from Git" → "GitHub"
3. Select your `full-stack-recipe` repository

### 2. Build Settings

1. **Build command:** `npm run build`
2. **Publish directory:** `dist`
3. **Base directory:** (leave empty)

### 3. Environment Variables

Add in Netlify dashboard:
```
VITE_BACKEND_URL=https://your-railway-url.up.railway.app
```

### 4. Deploy

1. Click "Deploy site"
2. Wait for build to complete
3. Your site will be available at `https://random-name.netlify.app`

## 🔗 Connect Frontend to Backend

### 1. Update API Configuration

In `src/config/api.ts`, update:
```typescript
export const RAILWAY_API_URL = 'https://your-actual-railway-url.up.railway.app';
```

### 2. Update CORS in Backend

In `backend/app_railway.py`, update:
```python
allowed_origins = [
    # ... existing origins ...
    "https://your-actual-netlify-url.netlify.app",
]
```

### 3. Redeploy Both

1. Push changes to GitHub
2. Railway will auto-deploy backend
3. Netlify will auto-deploy frontend

## 🆓 Free Tier Limitations

### Railway Free Tier
- 500 hours/month
- 512MB RAM
- 1GB storage
- Sleep after 15 minutes inactivity
- Auto-restart on failure

### Netlify Free Tier
- 100GB bandwidth/month
- Build time: 300 minutes/month
- Form submissions: 100/month
- Function invocations: 125K/month

## 🚨 Troubleshooting

### Railway Crashes
1. Check logs in Railway dashboard
2. Ensure environment variables are set
3. Verify Dockerfile is correct
4. Check memory usage (free tier limit: 512MB)

### Frontend Can't Connect
1. Verify CORS settings in backend
2. Check Railway URL is correct
3. Ensure backend is running
4. Check browser console for errors

### Build Failures
1. Check package.json dependencies
2. Verify Node.js version (18+)
3. Check for syntax errors
4. Review build logs

## 🔄 Continuous Deployment

Both Railway and Netlify will automatically deploy when you push to GitHub main branch.

## 📱 Testing

1. Test backend: Visit your Railway URL + `/api/health`
2. Test frontend: Visit your Netlify URL
3. Test connection: Frontend should load recipes from backend

## 💡 Optimization Tips

1. **Backend:**
   - Use minimal dependencies
   - Implement proper error handling
   - Add health checks
   - Use connection pooling

2. **Frontend:**
   - Optimize bundle size
   - Implement lazy loading
   - Use CDN for static assets
   - Add error boundaries

## 🆘 Support

- Railway: [Discord](https://discord.gg/railway)
- Netlify: [Community](https://community.netlify.com)
- GitHub Issues: For code-specific problems

---

**Happy Deploying! 🎉**
