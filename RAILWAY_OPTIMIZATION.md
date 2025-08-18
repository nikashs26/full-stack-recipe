# Railway Deployment Optimization Guide

## 🚀 Quick Deploy (Recommended)

The build timeout issue has been fixed by optimizing the deployment configuration:

### What Changed:
1. **Switched from Nixpacks to Docker** - Much faster builds
2. **Optimized requirements.txt** - Removed heavy AI dependencies
3. **Added .dockerignore** - Excludes unnecessary files
4. **Production-optimized Dockerfile** - Faster, smaller builds

### Deploy Steps:
1. **Commit and push** these changes to your repository
2. **Redeploy on Railway** - it will now use the optimized Docker build
3. **Build time** should be reduced from 10+ minutes to 2-3 minutes

## 🔧 Alternative: Manual Railway Setup

If you prefer to set up manually:

1. **In Railway dashboard:**
   - Go to your project
   - Click "Settings" → "Build & Deploy"
   - Change "Builder" from "Nixpacks" to "Dockerfile"
   - Set "Dockerfile Path" to `backend/Dockerfile`

2. **Environment Variables:**
   - Add your environment variables in Railway dashboard
   - Make sure `PORT` is set (Railway sets this automatically)

## 📦 What's Included in Production Build

### Core Dependencies:
- ✅ Flask & Flask-CORS
- ✅ Python-dotenv
- ✅ Requests
- ✅ Gunicorn
- ✅ ChromaDB

### Excluded (to reduce build time):
- ❌ sentence-transformers (2GB+ download)
- ❌ torch (Very large ML framework)
- ❌ openai (Large package with many deps)

## 🚨 Important Notes

### AI Features:
- If you need AI features in production, you'll need to add them back
- Consider using a separate AI service instead of embedding everything
- Or use lighter alternatives like `sentence-transformers` with pre-built models

### ChromaDB:
- ChromaDB data will be created at runtime
- Consider using Railway's persistent storage for production data

### Environment Variables:
Make sure these are set in Railway:
```bash
FLASK_ENV=production
JWT_SECRET=your_secret_here
# Add other required env vars
```

## 🔍 Troubleshooting

### Build Still Times Out:
1. Check if Dockerfile is being used (not Nixpacks)
2. Verify .dockerignore is excluding large files
3. Consider removing more dependencies temporarily

### App Won't Start:
1. Check Railway logs for errors
2. Verify environment variables are set
3. Ensure health check endpoint `/health` exists

### Performance Issues:
1. Monitor Railway metrics
2. Consider upgrading to a higher tier plan
3. Optimize database queries and caching

## 📈 Expected Results

- **Build Time**: 2-3 minutes (vs 10+ minutes before)
- **Image Size**: ~200-300MB (vs 2GB+ before)
- **Startup Time**: 10-30 seconds
- **Memory Usage**: Lower due to fewer dependencies

## 🆘 Need Help?

If you still encounter issues:
1. Check Railway build logs
2. Verify all files are committed
3. Try deploying to a new Railway project
4. Consider using Railway's CLI for debugging
