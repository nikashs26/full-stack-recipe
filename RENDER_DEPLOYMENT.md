# Render Deployment Guide

## 🚀 Quick Setup

### 1. **Deploy to Render**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository: `full-stack-recipe`
5. Configure:
   - **Name**: `full-stack-recipe-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan**: `Free`

### 2. **Set Environment Variables**
In Render dashboard:
1. Go to your service
2. Environment tab
3. Add these variables:

```
FLASK_SECRET_KEY=your-secret-key-here
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
JWT_SECRET_KEY=your-jwt-secret-key
CHROMA_DB_PATH=/opt/render/project/src/chroma_db
RAILWAY_ENVIRONMENT=true
```

### 3. **Update Frontend**
Update your frontend to use the new Render URL:
```javascript
const API_BASE_URL = 'https://your-service-name.onrender.com';
```

## 🔧 **What Changed**

- **Backend**: Moved from Railway to Render
- **Database**: Still using ChromaDB (local storage)
- **Deployment**: Automatic from GitHub pushes
- **Cost**: FREE (with 750 hours/month limit)

## 📁 **File Structure**
```
├── app.py                 # Main Flask app for Render
├── requirements.txt       # Python dependencies
├── render.yaml           # Render configuration
├── backend/              # Your existing Flask app
└── RENDER_DEPLOYMENT.md  # This guide
```

## ⚠️ **Render Free Tier Limits**
- **750 hours/month** (enough for 24/7 if only 1 service)
- **100GB bandwidth/month** (exceeding costs $30)
- **500 build minutes/month**
- **Services spin down after 15min inactivity**

## 🎯 **Next Steps**
1. Deploy to Render
2. Set environment variables
3. Update frontend API URLs
4. Test all functionality
5. Monitor bandwidth usage

## 🆓 **Why Render?**
- ✅ Free tier with generous limits
- ✅ Easy GitHub integration
- ✅ Automatic deployments
- ✅ Good for production apps
- ⚠️ Need credit card (for overage protection)
