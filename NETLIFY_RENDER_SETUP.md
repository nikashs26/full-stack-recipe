# 🌐 Netlify + Render Setup Guide

## ✅ **What's Been Updated**

Your frontend is now configured to work with your Render backend! Here's what changed:

### **Files Updated:**
- ✅ `src/config/api.ts` - Updated to use Render URL as default
- ✅ `netlify-env.example` - Updated example environment variables

---

## 🚀 **Deploy to Netlify**

### **Option 1: Automatic Deployment (Recommended)**
If your Netlify is connected to GitHub:

1. **Push your changes:**
   ```bash
   git add .
   git commit -m "Update frontend to use Render backend"
   git push origin main
   ```

2. **Netlify will automatically deploy** with the new Render URL

### **Option 2: Manual Deployment**
1. Build your frontend:
   ```bash
   npm run build
   ```

2. Deploy the `dist` folder to Netlify

---

## ⚙️ **Set Environment Variables in Netlify**

### **In Netlify Dashboard:**
1. Go to your site dashboard
2. **Site settings** → **Environment variables**
3. Add/Update this variable:

```bash
VITE_BACKEND_URL=https://dietary-delight.onrender.com
```

### **Why This Works:**
- Your frontend checks for `VITE_BACKEND_URL` first
- If not found, it falls back to the Render URL in `api.ts`
- This gives you flexibility to change backends without code changes

---

## 🔧 **Configuration Details**

### **Frontend (Netlify):**
- **URL**: Your Netlify URL (e.g., `https://betterbulk.netlify.app`)
- **Backend**: Points to `https://dietary-delight.onrender.com`

### **Backend (Render):**
- **URL**: `https://dietary-delight.onrender.com`
- **CORS**: Configured to allow your Netlify domain

### **Data Flow:**
```
Netlify Frontend → Render Backend → ChromaDB (file-based)
```

---

## 🧪 **Testing Your Setup**

### **1. Test Backend Health:**
```bash
curl https://dietary-delight.onrender.com/api/health
```

### **2. Test Frontend Connection:**
1. Open your Netlify site
2. Open browser dev tools (F12)
3. Check Network tab for API calls
4. Verify calls go to `dietary-delight.onrender.com`

### **3. Test Full Flow:**
1. Search for recipes
2. Check if results load from Render backend
3. Test user authentication
4. Test meal planning features

---

## 🔄 **Migration Steps**

### **If You Haven't Deployed Render Yet:**
1. **Deploy Render first** (follow `RENDER_DEPLOYMENT_COMPLETE.md`)
2. **Migrate your data** (run `migrate_to_render.py`)
3. **Deploy Netlify** (this guide)

### **If Render is Already Deployed:**
1. **Update Netlify environment variable** to point to Render
2. **Redeploy Netlify** (or wait for auto-deploy)

---

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **CORS Errors:**
   - Check if your Netlify URL is in Render's CORS allowed origins
   - Verify `VITE_BACKEND_URL` is set correctly

2. **API Calls Failing:**
   - Check browser dev tools Network tab
   - Verify Render backend is running
   - Check if data has been migrated

3. **Authentication Issues:**
   - Clear browser localStorage
   - Check if JWT tokens are being sent correctly

### **Debug Commands:**
```bash
# Check Render backend
curl https://dietary-delight.onrender.com/api/health

# Check Netlify frontend
curl https://your-netlify-site.netlify.app

# Test API connection
curl -H "Origin: https://your-netlify-site.netlify.app" \
     https://dietary-delight.onrender.com/api/health
```

---

## 🎉 **Success!**

Your setup is now:
- ✅ **Frontend**: Netlify (fast, global CDN)
- ✅ **Backend**: Render (cost-effective, reliable)
- ✅ **Database**: ChromaDB (file-based, no external service needed)

**Benefits:**
- 🚀 **Fast frontend** with Netlify's global CDN
- 💰 **Cost-effective backend** with Render's free tier
- 🔒 **Secure** with proper CORS configuration
- 📊 **All your data** preserved and migrated

---

## 🔄 **Rollback Plan**

If you need to switch back to Railway:
1. Update `VITE_BACKEND_URL` in Netlify to your Railway URL
2. Or update `RENDER_API_URL` in `src/config/api.ts` to Railway URL
3. Redeploy Netlify

Your frontend will automatically use the new backend URL!
