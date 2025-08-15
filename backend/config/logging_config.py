"""
Logging configuration for the backend to reduce chaotic output
"""

import logging
import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import logging_settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logging_settings import (
        DEBUG_MODE, LOG_LEVEL, SAVE_LOGS_TO_FILE, 
        SUPPRESS_EMOJI_LOGS, SUPPRESS_MODULES
    )
except ImportError:
    # Default values if settings file doesn't exist
    DEBUG_MODE = False
    LOG_LEVEL = 'WARNING'
    SAVE_LOGS_TO_FILE = True
    SUPPRESS_EMOJI_LOGS = True
    SUPPRESS_MODULES = []

def configure_logging(debug_mode: bool = None) -> None:
    """
    Configure logging for the backend application
    
    Args:
        debug_mode: If provided, overrides the setting from logging_settings.py
    """
    
    # Use provided debug_mode or fall back to settings file
    if debug_mode is None:
        debug_mode = DEBUG_MODE
    
    # Set base logging level
    if debug_mode:
        base_level = logging.DEBUG
    else:
        # Convert string level to logging constant
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        base_level = level_map.get(LOG_LEVEL, logging.WARNING)
    
    # Configure root logger
    handlers = [logging.StreamHandler()]
    
    if SAVE_LOGS_TO_FILE:
        handlers.append(logging.FileHandler('backend.log'))
    
    logging.basicConfig(
        level=base_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Suppress verbose logging from external libraries
    logging.getLogger('werkzeug').setLevel(logging.ERROR)  # Flask internal logs
    logging.getLogger('urllib3').setLevel(logging.ERROR)   # HTTP client logs
    logging.getLogger('chromadb').setLevel(logging.ERROR)  # ChromaDB logs
    logging.getLogger('requests').setLevel(logging.ERROR)  # HTTP requests
    logging.getLogger('httpx').setLevel(logging.ERROR)     # HTTP client
    
    # Suppress specific noisy modules
    for module in SUPPRESS_MODULES:
        logging.getLogger(module).setLevel(logging.ERROR)
    
    # Configure specific module logging levels
    module_levels: Dict[str, int] = {
        # Core services - only show important info
        'services.recipe_cache_service': logging.WARNING,
        'services.recipe_service': logging.WARNING,
        'services.user_preferences_service': logging.ERROR if not debug_mode else logging.INFO,
        'services.meal_planner_agent': logging.ERROR if not debug_mode else logging.INFO,
        'services.llm_meal_planner_agent': logging.ERROR if not debug_mode else logging.INFO,
        
        # Routes - only show errors
        'routes.temp_preferences': logging.ERROR,
        'routes.preferences': logging.ERROR,
        'routes.recipe_routes': logging.ERROR,
        'routes.auth_routes': logging.ERROR,
        
        # Test modules - suppress unless debug mode
        'test_ollama': logging.ERROR if not debug_mode else logging.INFO,
        'test_meal_planner': logging.ERROR if not debug_mode else logging.INFO,
    }
    
    # Apply module-specific logging levels
    for module, level in module_levels.items():
        logging.getLogger(module).setLevel(level)
    
    # Create a custom filter to suppress emoji-heavy debug messages
    if SUPPRESS_EMOJI_LOGS and not debug_mode:
        class EmojiFilter(logging.Filter):
            """Filter out messages with excessive emojis in non-debug mode"""
            
            def filter(self, record):
                # Count emojis in the message
                message = str(record.getMessage())
                emoji_count = sum(1 for char in message if ord(char) > 127 and char in '🔥✅❌⚠️📊🚀💡🍽️📋⚡')
                
                # If message has more than 2 emojis, suppress it unless it's an error
                if emoji_count > 2 and record.levelno < logging.ERROR:
                    return False
                
                return True
        
        # Apply the filter to the root logger
        root_logger = logging.getLogger()
        root_logger.addFilter(EmojiFilter())
    
    # Log configuration summary
    if debug_mode:
        print("🔍 Debug mode enabled - verbose logging active")
    else:
        print("🚀 Production mode - minimal logging, errors only")
        if SAVE_LOGS_TO_FILE:
            print("📝 Detailed logs saved to 'backend.log'")
        if SUPPRESS_EMOJI_LOGS:
            print("🚫 Emoji-heavy debug messages suppressed")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name and appropriate level
    
    Args:
        name: The name of the logger
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def set_debug_mode(debug: bool = False) -> None:
    """
    Dynamically change debug mode
    
    Args:
        debug: Whether to enable debug mode
    """
    configure_logging(debug)

def quick_fix_chaos():
    """
    Quick fix to immediately reduce chaotic logging
    """
    print("🚨 Quick fix: Reducing chaotic logging...")
    
    # Immediately suppress the noisiest modules
    for module in SUPPRESS_MODULES:
        logging.getLogger(module).setLevel(logging.ERROR)
    
    # Suppress external library noise
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('chromadb').setLevel(logging.ERROR)
    
    print("✅ Chaotic logging reduced! Restart server for full effect.")
