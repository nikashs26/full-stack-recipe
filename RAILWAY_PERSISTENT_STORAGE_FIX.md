# Railway Persistent Storage Fix

## Problem
- Recipes disappear after every Railway deployment/commit
- User preferences are not saved and don't persist
- ChromaDB data is stored in ephemeral container filesystem

## Root Cause
Railway containers are ephemeral - when you commit changes, Railway rebuilds and redeploys the container, which wipes out all data including the `./chroma_db` directory.

## Solution: Railway Persistent Volumes

### 1. Railway Configuration
Updated `railway.toml` to include persistent volume:
```toml
[[volumes]]
mountPath = "/app/data"
```

### 2. ChromaDB Path Configuration
All ChromaDB services now use environment-based path configuration:

- **Local Development**: `./chroma_db` (default)
- **Railway Production**: `/app/data/chroma_db` (persistent volume)

### 3. Environment Variables
Set in Railway dashboard or `app_railway.py`:
- `RAILWAY_ENVIRONMENT=true`
- `CHROMA_DB_PATH=/app/data/chroma_db`

### 4. Updated Services
All ChromaDB services now use persistent storage:
- `RecipeCacheService` - Recipe storage
- `UserPreferencesService` - User preferences
- `ReviewService` - Recipe reviews
- `UserService` - User data
- `FolderService` - Recipe folders
- `MealHistoryService` - Meal history
- `SmartShoppingService` - Shopping lists
- `RecipeSearchService` - Search functionality

## Deployment Steps

### 1. Deploy with Persistent Volume
1. Commit the changes to your repository
2. Railway will automatically detect the `railway.toml` volume configuration
3. The persistent volume will be mounted at `/app/data`

### 2. Populate Data
After deployment, populate the database:
```bash
# Trigger population via API
curl -X POST https://your-railway-app.up.railway.app/api/populate-async

# Check status
curl https://your-railway-app.up.railway.app/api/populate-status
```

### 3. Verify Persistence
1. Check recipe count: `curl https://your-railway-app.up.railway.app/api/debug-recipes`
2. Check preferences: `curl https://your-railway-app.up.railway.app/api/preferences-status`
3. Make a test commit and redeploy
4. Verify data still exists after redeployment

## Alternative: External Database
If persistent volumes don't work, consider using Railway's managed database services:

### PostgreSQL Option
1. Add PostgreSQL service in Railway dashboard
2. Update services to use PostgreSQL instead of ChromaDB
3. Use environment variables: `DATABASE_URL`, `PGHOST`, etc.

### MongoDB Option
1. Add MongoDB service in Railway dashboard
2. Update services to use MongoDB
3. Use environment variables: `MONGODB_URI`

## Testing
After deployment, test that:
1. ✅ Recipes persist across deployments
2. ✅ User preferences are saved and loaded
3. ✅ Search functionality works
4. ✅ Meal planning works
5. ✅ All user data persists

## Troubleshooting

### Volume Not Mounting
- Check Railway dashboard for volume status
- Verify `railway.toml` configuration
- Check container logs for mount errors

### Permission Issues
- Ensure `/app/data` directory has correct permissions
- Check if `RAILWAY_RUN_UID=0` is needed

### Data Not Persisting
- Verify volume is mounted correctly
- Check if ChromaDB is using the correct path
- Look for errors in application logs

## Benefits
- ✅ Data persists across deployments
- ✅ No need to rerun population scripts
- ✅ User preferences work correctly
- ✅ All app features function properly
- ✅ Scalable and production-ready
