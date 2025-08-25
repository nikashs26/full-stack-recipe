# Netlify + Railway Deployment Fix Guide

## Issues Identified and Fixed

### 1. Backend Routes Missing
- **Problem**: `app_railway.py` only had basic health check routes
- **Fix**: Added all necessary routes (preferences, meal planner, recipes, auth, etc.)
- **File**: `backend/app_railway.py`

### 2. Missing Dependencies
- **Problem**: Railway requirements were minimal, missing ChromaDB and other services
- **Fix**: Updated `requirements-railway.txt` with complete dependencies
- **File**: `backend/requirements-railway.txt`

### 3. CORS Configuration
- **Problem**: CORS origins didn't match actual Netlify URL
- **Fix**: Updated CORS to allow all Netlify subdomains and proper HTTPS settings
- **File**: `backend/app_railway.py`

### 4. Environment Variables
- **Problem**: No VITE_BACKEND_URL configured for Netlify
- **Fix**: Created environment variable examples and updated API config
- **Files**: `netlify-env.example`, `src/config/api.ts`

## Deployment Steps

### Step 1: Update Railway Backend
1. Commit and push the updated `app_railway.py` and `requirements-railway.txt`
2. Railway will automatically redeploy with the new configuration
3. Check Railway logs to ensure all routes are registered successfully

### Step 2: Configure Netlify Environment Variables
1. Go to your Netlify dashboard
2. Navigate to Site settings > Environment variables
3. Add the following variables:
   ```
   VITE_BACKEND_URL=https://your-railway-url.up.railway.app
   ```
4. Replace `your-railway-url` with your actual Railway project URL

### Step 3: Redeploy Netlify
1. Trigger a new deployment in Netlify
2. The build will now use the correct backend URL
3. Check that preferences, meal planner, and recipes are working

### Step 4: Verify Backend Health
1. Test your Railway backend health endpoint:
   ```
   https://your-railway-url.up.railway.app/api/health
   ```
2. Should return: `{"status": "healthy", "message": "Railway backend is running", "routes": "all registered"}`

## Expected Results After Fix

- ✅ All recipes should load properly from ChromaDB
- ✅ Preferences page should work with backend API calls
- ✅ Meal planner should function with backend integration
- ✅ Authentication should work properly
- ✅ CORS errors should be resolved

## Troubleshooting

### If recipes still don't load:
1. Check Railway logs for ChromaDB initialization errors
2. Verify ChromaDB data is properly indexed
3. Check if Railway has enough memory for ChromaDB

### If preferences/meal planner still don't work:
1. Verify environment variable `VITE_BACKEND_URL` is set correctly
2. Check browser console for CORS or API errors
3. Test backend endpoints directly

### If build fails:
1. Ensure all dependencies are in `requirements-railway.txt`
2. Check Railway logs for Python import errors
3. Verify file paths and imports in `app_railway.py`

## Files Modified

- `backend/app_railway.py` - Added all routes and proper CORS
- `backend/requirements-railway.txt` - Complete dependencies
- `src/config/api.ts` - Better environment variable handling
- `netlify.toml` - Improved build configuration
- `netlify-env.example` - Environment variable template
- `NETLIFY_RAILWAY_DEPLOYMENT_FIX.md` - This guide

## Next Steps

1. Deploy the updated backend to Railway
2. Set environment variables in Netlify
3. Redeploy frontend to Netlify
4. Test all functionality
5. Monitor Railway logs for any remaining issues
