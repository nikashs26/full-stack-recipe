#!/usr/bin/env python3
"""
Automated ChromaDB Backup Script

This script creates a backup of ChromaDB and can be run as a cron job.
It automatically creates timestamped backups and cleans up old ones.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the backup functions
from backup_chromadb import create_backup, list_backups, get_backup_dir

def auto_backup(max_backups: int = 10, cleanup_old: bool = True):
    """Create an automated backup with optional cleanup"""
    
    print(f"🤖 Automated ChromaDB backup started at {datetime.now().isoformat()}")
    
    try:
        # Create backup
        backup_path = create_backup("auto_backup")
        print(f"✅ Automated backup created: {backup_path}")
        
        # Cleanup old backups if requested
        if cleanup_old:
            cleanup_old_backups(max_backups)
        
        return True
        
    except Exception as e:
        print(f"❌ Automated backup failed: {e}")
        return False

def cleanup_old_backups(max_backups: int = 10):
    """Remove old backups, keeping only the most recent ones"""
    
    backup_dir = get_backup_dir()
    backups = list_backups()
    
    if len(backups) <= max_backups:
        print(f"📚 No cleanup needed. Have {len(backups)} backups, max allowed: {max_backups}")
        return
    
    # Sort by timestamp (oldest first for deletion)
    backups.sort(key=lambda x: x["metadata"].get("backup_timestamp", ""))
    
    # Calculate how many to delete
    to_delete = len(backups) - max_backups
    print(f"🧹 Cleaning up {to_delete} old backups...")
    
    deleted_count = 0
    for backup in backups[:to_delete]:
        try:
            backup_file = Path(backup["path"])
            if backup_file.exists():
                backup_file.unlink()
                print(f"🗑️ Deleted: {backup['filename']}")
                deleted_count += 1
        except Exception as e:
            print(f"⚠️ Could not delete {backup['filename']}: {e}")
    
    print(f"✅ Cleanup completed. Deleted {deleted_count} backups.")
    print(f"📚 Kept {len(backups) - deleted_count} most recent backups.")

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated ChromaDB backup")
    parser.add_argument("--max-backups", type=int, default=10, 
                       help="Maximum number of backups to keep (default: 10)")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Skip cleanup of old backups")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress output (useful for cron jobs)")
    
    args = parser.parse_args()
    
    if args.quiet:
        # Redirect output to /dev/null for cron jobs
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    
    success = auto_backup(
        max_backups=args.max_backups,
        cleanup_old=not args.no_cleanup
    )
    
    # Exit with appropriate code for cron jobs
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 