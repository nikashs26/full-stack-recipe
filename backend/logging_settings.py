# Backend Logging Settings
# Change these values to control logging behavior

# Set to True for verbose logging, False for minimal logging
DEBUG_MODE = False

# Log level when DEBUG_MODE is False
# Options: 'INFO', 'WARNING', 'ERROR'
LOG_LEVEL = 'WARNING'

# Save detailed logs to file instead of console
SAVE_LOGS_TO_FILE = True

# Suppress emoji-heavy debug messages
SUPPRESS_EMOJI_LOGS = True

# Suppress specific noisy modules
SUPPRESS_MODULES = [
    'routes.temp_preferences',
    'routes.preferences', 
    'services.user_preferences_service',
    'services.meal_planner_agent',
    'services.llm_meal_planner_agent'
]
