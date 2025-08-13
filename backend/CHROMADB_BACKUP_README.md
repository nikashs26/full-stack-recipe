# ChromaDB Backup & Restore System

This directory contains a comprehensive backup and restore solution for your ChromaDB data. ChromaDB stores your recipe embeddings, search indexes, and metadata, so regular backups are essential.

## 🚀 Quick Start

### Create Your First Backup

```bash
cd backend
python3 backup_chromadb.py
```

Choose option 1 to create a backup. The script will:
- Create a timestamped backup
- Compress it into a ZIP file
- Store it in `chromadb_backups/` directory
- Show detailed metadata about what was backed up

### List All Backups

```bash
python3 backup_chromadb.py
```

Choose option 2 to see all available backups with their timestamps, sizes, and collection information.

## 📁 Files Overview

- **`backup_chromadb.py`** - Main backup/restore tool with interactive menu
- **`auto_backup_chromadb.py`** - Automated backup script for cron jobs
- **`chromadb_backups/`** - Directory where all backups are stored
- **`CHROMADB_BACKUP_README.md`** - This documentation

## 🔧 Manual Backup Operations

### Interactive Backup Tool

```bash
python3 backup_chromadb.py
```

**Options:**
1. **Create backup** - Create a new backup with optional custom name
2. **List backups** - View all available backups
3. **Show backup info** - Detailed information about a specific backup
4. **Restore backup** - Restore ChromaDB from a backup
5. **Exit** - Close the tool

### Command Line Backup

```bash
# Create backup with custom name
python3 backup_chromadb.py

# Or use the automated script
python3 auto_backup_chromadb.py --max-backups 15
```

## 🤖 Automated Backups

### Using Cron (Linux/macOS)

Set up automatic daily backups:

```bash
# Edit crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * cd /path/to/your/backend && python3 auto_backup_chromadb.py --quiet --max-backups 30

# Or weekly backup on Sundays at 3 AM
0 3 * * 0 cd /path/to/your/backend && python3 auto_backup_chromadb.py --quiet --max-backups 10
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Set action: `python.exe auto_backup_chromadb.py --quiet --max-backups 30`
5. Set working directory to your backend folder

### Automated Script Options

```bash
# Basic automated backup
python3 auto_backup_chromadb.py

# Keep more backups (30 instead of default 10)
python3 auto_backup_chromadb.py --max-backups 30

# Skip cleanup of old backups
python3 auto_backup_chromadb.py --no-cleanup

# Quiet mode for cron jobs (no output)
python3 auto_backup_chromadb.py --quiet
```

## 🔄 Restore Operations

### Restore from Backup

```bash
python3 backup_chromadb.py
```

Choose option 4, then select the backup to restore from.

**⚠️ Important:** Restoring will overwrite your current ChromaDB data. The system will:
1. Create a backup of your current data before restoring
2. Ask for confirmation before proceeding
3. Restore the selected backup
4. Verify the restoration

### Force Restore

If you need to restore without prompts:

```bash
# In the interactive tool, choose 'y' when asked about force restore
# Or modify the script to set force=True
```

## 📊 Backup Contents

Each backup contains:

- **Complete ChromaDB data** - All collections, embeddings, and metadata
- **Backup metadata** - Timestamp, collection info, file counts, sizes
- **Compressed format** - ZIP file for easy storage and transfer

### What Gets Backed Up

- Recipe embeddings and search indexes
- Collection metadata and configurations
- SQLite databases and index files
- All ChromaDB internal structures

### What's NOT Backed Up

- Your application code
- Configuration files
- Log files
- Temporary files

## 🗂️ Backup Storage

### Local Storage

Backups are stored in `backend/chromadb_backups/` with names like:
- `chromadb_backup_20241220_143022.zip`
- `auto_backup_20241220_143022.zip`
- `custom_name_20241220_143022.zip`

### External Storage (Recommended)

For production use, consider:

1. **Cloud Storage** (AWS S3, Google Cloud, etc.)
2. **Network Attached Storage (NAS)**
3. **External hard drives**
4. **Git repositories** (for small databases)

### Backup Rotation

The automated script keeps only the most recent N backups (default: 10). You can adjust this with `--max-backups`.

## 🚨 Best Practices

### Backup Frequency

- **Development**: Weekly or before major changes
- **Production**: Daily automated backups
- **Critical updates**: Manual backup before changes

### Backup Verification

1. **Test restores** periodically on a test environment
2. **Verify backup sizes** are consistent
3. **Check collection counts** in backup metadata
4. **Monitor backup success** in logs

### Storage Strategy

1. **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
2. **Version control**: Keep multiple backup versions
3. **Regular testing**: Verify restore functionality
4. **Documentation**: Keep backup procedures documented

## 🔍 Troubleshooting

### Common Issues

**Backup fails with "ChromaDB in use"**
- Stop your application before backing up
- Or use the automated script during off-hours

**Restore fails with "permission denied"**
- Ensure you have write permissions to the ChromaDB directory
- Check if ChromaDB is currently running

**Backup file is corrupted**
- Try extracting the ZIP manually
- Check disk space and file system integrity
- Re-run the backup

**Collection count mismatch**
- This is normal if you've added/removed recipes since backup
- The backup contains the state at backup time

### Debug Mode

For troubleshooting, you can modify the scripts to add more logging:

```python
# In backup_chromadb.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Monitoring & Alerts

### Log Monitoring

Check backup logs for:
- Successful backup completions
- Failed backup attempts
- Cleanup operations
- Restore operations

### Alert Setup

Consider setting up alerts for:
- Failed backups
- Backup size anomalies
- Disk space issues
- Restore operations

## 🔐 Security Considerations

### Backup Access

- **Restrict access** to backup files
- **Encrypt sensitive data** if needed
- **Use secure storage** for production backups
- **Audit backup access** regularly

### Data Privacy

- **Review backup contents** for sensitive information
- **Comply with data regulations** (GDPR, etc.)
- **Secure backup storage** with appropriate access controls

## 📞 Support

If you encounter issues:

1. **Check the logs** for error messages
2. **Verify file permissions** and disk space
3. **Test with a small backup** first
4. **Review this documentation** for common solutions

## 🎯 Next Steps

1. **Create your first backup** using the interactive tool
2. **Set up automated backups** with cron or Task Scheduler
3. **Test restore functionality** in a safe environment
4. **Implement backup monitoring** and alerting
5. **Document your backup procedures** for your team

Remember: **A backup is only as good as your ability to restore from it!** 