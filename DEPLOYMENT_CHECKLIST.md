# 🚀 Deployment Checklist

## ✅ Pre-Deployment Checks

- [ ] All files are committed to GitHub
- [ ] Railway account is set up and connected to GitHub
- [ ] Netlify account is set up and connected to GitHub
- [ ] Environment variables are ready

## 🔧 Railway Backend Deployment

### 1. Railway Dashboard Setup
- [ ] Go to [Railway.app](https://railway.app)
- [ ] Click "New Project" → "Deploy from GitHub repo"
- [ ] Select your `full-stack-recipe` repository
- [ ] **IMPORTANT**: Do NOT set a source directory (leave empty)
- [ ] Railway will use the root `Dockerfile`

### 2. Environment Variables
Add these in Railway dashboard:
- [ ] `FLASK_SECRET_KEY=your-super-secret-key-here`
- [ ] `DEBUG=false`

### 3. Deploy
- [ ] Click "Deploy"
- [ ] Wait for build to complete
- [ ] Copy your Railway URL (e.g., `https://your-app-name-production.up.railway.app`)

## 🌐 Netlify Frontend Deployment

### 1. Netlify Setup
- [ ] Go to [Netlify.com](https://netlify.com)
- [ ] Click "New site from Git" → "GitHub"
- [ ] Select your `full-stack-recipe` repository

### 2. Build Settings
- [ ] Build command: `npm run build`
- [ ] Publish directory: `dist`
- [ ] Base directory: (leave empty)

### 3. Environment Variables
Add in Netlify dashboard:
- [ ] `VITE_BACKEND_URL=https://your-railway-url.up.railway.app`

### 4. Deploy
- [ ] Click "Deploy site"
- [ ] Wait for build to complete
- [ ] Copy your Netlify URL

## 🔗 Connect Frontend to Backend

### 1. Update API Configuration
- [ ] In `src/config/api.ts`, update `RAILWAY_API_URL` with your actual Railway URL
- [ ] Commit and push changes

### 2. Update CORS in Backend
- [ ] In `backend/app_railway.py`, update CORS origins with your actual Netlify URL
- [ ] Commit and push changes

### 3. Test Connection
- [ ] Test backend: Visit Railway URL + `/api/health`
- [ ] Test frontend: Visit Netlify URL
- [ ] Verify frontend can load data from backend

## 🧪 Testing

### Backend Health Check
```bash
# Test your Railway backend
curl https://your-railway-url.up.railway.app/api/health
```

### Frontend Connection Test
1. Open browser console on your Netlify site
2. Check for any CORS or connection errors
3. Verify API calls are going to Railway URL

## 🚨 Troubleshooting

### Railway Issues
- [ ] Check Railway logs for build errors
- [ ] Verify Dockerfile path is correct
- [ ] Check memory usage (free tier: 512MB)
- [ ] Ensure environment variables are set

### Netlify Issues
- [ ] Check build logs for errors
- [ ] Verify build command and publish directory
- [ ] Check environment variables are set
- [ ] Verify Node.js version (18+)

### Connection Issues
- [ ] Verify CORS origins in backend
- [ ] Check Railway URL is correct in frontend
- [ ] Ensure both services are running
- [ ] Check browser console for errors

## 🎯 Success Indicators

✅ Backend responds to `/api/health`  
✅ Frontend loads without errors  
✅ Frontend can fetch data from backend  
✅ No CORS errors in browser console  
✅ Both services show as "deployed" in their dashboards  

## 📞 Need Help?

- **Railway**: [Discord](https://discord.gg/railway)
- **Netlify**: [Community](https://community.netlify.com)
- **This Project**: Check `RAILWAY_DEPLOYMENT_GUIDE.md`

---

**Happy Deploying! 🎉**
