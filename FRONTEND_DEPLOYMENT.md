# 🎨 Frontend Deployment Guide

## **Option 1: Netlify (Recommended)**

### **Step 1: Build Your App**
```bash
cd src
npm run build
```

### **Step 2: Deploy to Netlify**
1. Go to [netlify.com](https://netlify.com)
2. Sign up/Login with GitHub
3. Click "New site from Git"
4. Connect your GitHub repository
5. Set build settings:
   - **Build command**: `cd src && npm run build`
   - **Publish directory**: `src/dist`
6. Click "Deploy site"

### **Step 3: Update API URLs**
After deployment, update your frontend API calls to use your Railway backend URL:

```typescript
// In src/config/api.ts
export const API_BASE_URL = 'https://your-app.railway.app';
```

## **Option 2: Vercel**

### **Step 1: Install Vercel CLI**
```bash
npm install -g vercel
```

### **Step 2: Deploy**
```bash
cd src
vercel
```

## **Option 3: GitHub Pages**

### **Step 1: Add GitHub Pages Script**
```json
// In package.json
{
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
  }
}
```

### **Step 2: Install gh-pages**
```bash
npm install --save-dev gh-pages
```

### **Step 3: Deploy**
```bash
npm run deploy
```

## **🔧 Environment Variables**

Create a `.env.production` file in your `src` directory:

```env
VITE_API_BASE_URL=https://your-app.railway.app
VITE_APP_ENV=production
```

## **📱 Custom Domain (Optional)**

1. Buy a domain (Namecheap, GoDaddy, etc.)
2. Add it to your hosting provider
3. Update DNS settings
4. Update CORS origins in your backend

## **🚀 After Deployment**

1. **Test your app** - Make sure all API calls work
2. **Update CORS** - Add your frontend URL to backend CORS origins
3. **Monitor logs** - Check Railway dashboard for any errors
4. **Set up monitoring** - Consider adding error tracking (Sentry, LogRocket)
