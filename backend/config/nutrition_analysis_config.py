"""
Configuration file for the Nutrition Analysis Agent.
Modify these settings to customize the behavior of the agent.
"""

# LLM Service Configuration
LLM_SERVICES = {
    'openai': {
        'enabled': True,
        'priority': 1,  # 1 = highest priority
        'model': 'gpt-3.5-turbo',
        'temperature': 0.1,
        'max_tokens': 200,
        'timeout': 30
    },
    'ollama': {
        'enabled': True,
        'priority': 2,
        'model': 'llama3.2:latest',
        'timeout': 30,
        'url': 'http://localhost:11434'
    },
    'huggingface': {
        'enabled': True,
        'priority': 3,
        'model': 'microsoft/DialoGPT-medium',
        'timeout': 30,
        'max_length': 200,
        'temperature': 0.1
    }
}

# Processing Configuration
PROCESSING_CONFIG = {
    'batch_size': 3,  # Number of recipes to process simultaneously
    'batch_delay': 1,  # Delay between batches in seconds
    'max_retries': 2,  # Maximum retry attempts for failed analyses
    'timeout': 60,     # Overall timeout for analysis operations
}

# Nutrition Validation Configuration
NUTRITION_VALIDATION = {
    'calories': {
        'min': 0,
        'max': 5000,  # Maximum calories per serving
        'unit': 'kcal'
    },
    'carbohydrates': {
        'min': 0,
        'max': 200,   # Maximum carbs per serving
        'unit': 'g'
    },
    'fat': {
        'min': 0,
        'max': 100,   # Maximum fat per serving
        'unit': 'g'
    },
    'protein': {
        'min': 0,
        'max': 100,   # Maximum protein per serving
        'unit': 'g'
    },
    'macro_consistency': {
        'enabled': True,
        'variance_tolerance': 0.5,  # 50% variance allowed between calories and macro calculations
        'calories_per_carb': 4,     # Calories per gram of carbohydrate
        'calories_per_fat': 9,      # Calories per gram of fat
        'calories_per_protein': 4   # Calories per gram of protein
    }
}

# Output Configuration
OUTPUT_CONFIG = {
    'save_detailed_results': True,
    'save_summary': True,
    'save_logs': True,
    'output_directory': './nutrition_analysis_output',
    'file_prefix': 'nutrition_analysis',
    'include_timestamps': True,
    'compress_output': False  # Set to True to gzip output files
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_handler': True,
    'console_handler': True,
    'log_file': 'nutrition_analysis.log',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Recipe Processing Configuration
RECIPE_PROCESSING = {
    'required_fields': ['id', 'title', 'ingredients', 'instructions'],
    'optional_fields': ['servings', 'cuisine', 'diet', 'prep_time', 'cook_time'],
    'ingredient_format': {
        'preferred': 'structured',  # 'structured' or 'text'
        'fallback_to_text': True
    },
    'instruction_format': {
        'preferred': 'list',  # 'list' or 'text'
        'fallback_to_text': True
    }
}

# LLM Prompt Configuration
PROMPT_CONFIG = {
    'system_prompt': """You are a nutrition expert with extensive knowledge of food composition and nutritional analysis. 
Your task is to analyze recipes and provide accurate nutritional information per serving.

Guidelines:
- Provide nutritional values per single serving
- Use standard units: calories (kcal), carbohydrates (g), fat (g), protein (g)
- Consider cooking methods and ingredient preparation
- Account for typical portion sizes and cooking losses
- Provide realistic, practical estimates

Always respond with valid JSON containing exactly these keys: calories, carbohydrates, fat, protein""",
    
    'user_prompt_template': """Recipe: {title}
Servings: {servings}

Ingredients:
{ingredients}

Instructions:
{instructions}

Please analyze this recipe and provide the following nutritional information per serving:
- Calories (kcal)
- Carbohydrates (g)
- Fat (g)
- Protein (g)

Provide the response in JSON format with these exact keys: calories, carbohydrates, fat, protein""",
    
    'response_format': {
        'required_keys': ['calories', 'carbohydrates', 'fat', 'protein'],
        'data_types': {
            'calories': 'float',
            'carbohydrates': 'float',
            'fat': 'float',
            'protein': 'float'
        },
        'precision': 1  # Decimal places for numeric values
    }
}

# Error Handling Configuration
ERROR_HANDLING = {
    'continue_on_failure': True,  # Continue processing other recipes if one fails
    'log_failures': True,         # Log detailed failure information
    'retry_failed': False,        # Whether to retry failed recipes
    'max_consecutive_failures': 10,  # Stop if too many consecutive failures
    'failure_threshold': 0.8      # Stop if success rate drops below this threshold
}

# Performance Monitoring
PERFORMANCE_MONITORING = {
    'enabled': True,
    'track_timing': True,
    'track_success_rates': True,
    'track_llm_service_usage': True,
    'generate_performance_report': True,
    'performance_report_file': 'nutrition_analysis_performance.json'
}

# Cache Integration Configuration
CACHE_INTEGRATION = {
    'update_existing_recipes': True,  # Update recipes that already have nutrition data
    'preserve_existing_nutrition': False,  # Keep existing nutrition data if present
    'add_metadata': True,  # Add analysis metadata to recipes
    'metadata_fields': [
        'nutrition_analyzed_at',
        'nutrition_llm_service',
        'nutrition_confidence_score'
    ]
}

# Export Configuration
EXPORT_CONFIG = {
    'formats': ['json', 'csv'],  # Export formats
    'include_metadata': True,    # Include analysis metadata in exports
    'group_by_status': True,     # Group results by success/error status
    'create_summary_report': True,
    'summary_report_formats': ['json', 'html']
} 