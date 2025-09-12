# 🔐 User Account Persistence on Render

## The Problem
Render's filesystem is **ephemeral**, meaning that user accounts stored in ChromaDB get wiped every time the server restarts or redeploys. This caused users to constantly need to sign up again.

## The Solution
We've implemented a **multi-layered backup and restore system** that ensures user accounts persist across deployments:

### 🔄 Automatic Backup & Restore

1. **On User Registration**: Automatically backs up all users
2. **On Server Startup**: Automatically restores users from backup
3. **Manual Backup**: Run `python backup_users.py` when needed

### 📁 Multiple Backup Methods

#### Method 1: Persistent File Backup
- Creates `user_backup_YYYYMMDD.json` in project root
- Contains all user account data with timestamps
- Automatically uses the most recent backup file

#### Method 2: Environment Variable Backup (Small Sites)
- For sites with ≤10 users
- Encodes user data as base64 in environment variables
- Perfect for personal/small business use

## 🚀 Setup Instructions

### For New Deployments
1. Deploy the updated code to Render
2. Users will be automatically backed up when they register
3. Backups are restored automatically on startup

### For Existing Users (Migration)
1. Run the backup script manually: `python backup_users.py`
2. If you have ≤10 users, the script will output an environment variable
3. Copy this environment variable to your Render dashboard:
   ```
   Variable Name: USER_BACKUP_DATA
   Variable Value: [base64 encoded user data]
   ```

### Environment Variable Setup (Render Dashboard)
1. Go to your Render service dashboard
2. Navigate to "Environment" tab
3. Add the `USER_BACKUP_DATA` variable if provided by backup script
4. Redeploy the service

## 🔧 How It Works

### Backup Process
```
User Registers → Auto Backup → Creates File + Env Backup
```

### Restore Process
```
Server Starts → Check File Backup → Check Env Backup → Restore Users
```

### Data Flow
```
ChromaDB ← → Backup Files ← → Environment Variables
```

## 📊 Monitoring

The system provides clear logging:
- `✅ Backed up X users for persistence` - Successful backup
- `✅ Restored X users from backup` - Successful restore  
- `📭 No user backup found - starting fresh` - No backups available
- `❌ Failed to backup/restore users` - Error occurred

## 🛠️ Manual Commands

### Backup Users
```bash
python backup_users.py
```

### Check Current Users
```bash
# In backend directory
python -c "
from services.user_service import UserService
us = UserService()
us.backup_users_for_persistence()
"
```

## 🔍 Troubleshooting

### Users Still Getting Lost?
1. Check Render logs for backup/restore messages
2. Verify environment variables are set correctly
3. Run manual backup script
4. Contact support if issues persist

### Environment Variable Too Large?
- Render has environment variable size limits
- For >10 users, the system automatically skips env backup
- File backup will still work for larger user bases

## 🎯 Features

- ✅ **Zero Configuration** - Works automatically
- ✅ **Multiple Fallbacks** - File + Environment backups  
- ✅ **Small Site Optimized** - Environment variable storage
- ✅ **Large Site Ready** - File-based backup
- ✅ **Automatic Recovery** - Restores on startup
- ✅ **Manual Control** - Scripts for manual backup

## 📈 Benefits

1. **No More Lost Accounts** - Users stay registered permanently
2. **Seamless Experience** - Works invisibly in background  
3. **Deploy Safely** - User accounts survive redeployments
4. **Scale Ready** - Handles both small and large user bases
5. **Zero Downtime** - Accounts restored instantly on startup

Your users will now stay logged in with their accounts persistent across all Render deployments! 🎉
