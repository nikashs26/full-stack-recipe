# Vercel Deployment Guide

## 🚀 Quick Setup

### 1. **Deploy to Vercel**
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from your project directory
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? (your account)
# - Link to existing project? No
# - Project name: full-stack-recipe-backend
# - Directory: ./
# - Override settings? No
```

### 2. **Set Environment Variables**
In Vercel dashboard:
1. Go to your project
2. Settings → Environment Variables
3. Add these variables:

```
FLASK_SECRET_KEY=your-secret-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
JWT_SECRET_KEY=your-jwt-secret-key
```

### 3. **Update Frontend**
Update your frontend to use the new Vercel URL:
```javascript
const API_BASE_URL = 'https://your-project.vercel.app/api';
```

## 🔧 **What Changed**

- **Backend**: Moved from Railway to Vercel serverless functions
- **Database**: Will migrate from ChromaDB to Supabase (next step)
- **Deployment**: Automatic from GitHub pushes
- **Cost**: 100% FREE forever!

## 📁 **File Structure**
```
├── api/
│   ├── index.py          # Main Vercel handler
│   └── requirements.txt  # Python dependencies
├── backend/              # Your existing Flask app
├── vercel.json          # Vercel configuration
└── vercel-env.example   # Environment variables template
```

## 🎯 **Next Steps**
1. Deploy to Vercel
2. Set up Supabase database
3. Update frontend API URLs
4. Test all functionality

## 🆓 **Why Vercel?**
- ✅ 100% free forever
- ✅ No credit card required
- ✅ No surprise charges
- ✅ Automatic deployments
- ✅ Global CDN
- ✅ Serverless functions
