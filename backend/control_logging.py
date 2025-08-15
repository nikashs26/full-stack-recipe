#!/usr/bin/env python3
"""
Simple script to control backend logging levels
"""

import os
import sys

def set_logging_level(level: str):
    """
    Set the logging level by updating environment variable
    
    Args:
        level: 'debug', 'info', 'warning', or 'error'
    """
    level = level.lower()
    
    if level == 'debug':
        os.environ['DEBUG'] = 'true'
        print("🔍 Debug mode enabled - verbose logging active")
    elif level == 'info':
        os.environ['DEBUG'] = 'false'
        os.environ['LOG_LEVEL'] = 'INFO'
        print("ℹ️  Info mode enabled - moderate logging")
    elif level == 'warning':
        os.environ['DEBUG'] = 'false'
        os.environ['LOG_LEVEL'] = 'WARNING'
        print("⚠️  Warning mode enabled - minimal logging")
    elif level == 'error':
        os.environ['DEBUG'] = 'false'
        os.environ['LOG_LEVEL'] = 'ERROR'
        print("❌ Error mode enabled - errors only")
    else:
        print(f"❌ Unknown logging level: {level}")
        print("Available levels: debug, info, warning, error")
        return
    
    print(f"✅ Logging level set to: {level}")
    print("🔄 Restart your backend server to apply changes")

def show_current_level():
    """Show the current logging configuration"""
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    log_level = os.environ.get('LOG_LEVEL', 'WARNING')
    
    print("📊 Current logging configuration:")
    print(f"   DEBUG: {debug}")
    print(f"   LOG_LEVEL: {log_level}")
    
    if debug:
        print("   🔍 Debug mode: Verbose logging active")
    else:
        print(f"   📝 Production mode: {log_level} level logging")

def main():
    if len(sys.argv) < 2:
        print("🎯 Backend Logging Control")
        print("Usage:")
        print("  python control_logging.py <level>")
        print("  python control_logging.py show")
        print("")
        print("Available levels:")
        print("  debug   - Verbose logging (chaotic but detailed)")
        print("  info    - Moderate logging")
        print("  warning - Minimal logging (recommended)")
        print("  error   - Errors only (very quiet)")
        print("  show    - Show current configuration")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_current_level()
    else:
        set_logging_level(command)

if __name__ == "__main__":
    main()
