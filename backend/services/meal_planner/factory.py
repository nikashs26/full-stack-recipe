from typing import Optional, Type, Dict, Any
from enum import Enum
import logging
from .base import BaseMealPlanner
from .openai_planner import OpenAIMealPlanner
from .ollama_planner import OllamaMealPlanner
from .huggingface_planner import HuggingFaceMealPlanner
from .fallback_planner import FallbackMealPlanner

logger = logging.getLogger(__name__)

class PlannerType(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    FALLBACK = "fallback"

class MealPlannerFactory:
    """Factory for creating meal planner instances based on configuration."""
    
    _planner_classes = {
        PlannerType.OPENAI: OpenAIMealPlanner,
        PlannerType.OLLAMA: OllamaMealPlanner,
        PlannerType.HUGGINGFACE: HuggingFaceMealPlanner,
        PlannerType.FALLBACK: FallbackMealPlanner,
    }
    
    @classmethod
    def create_planner(
        cls,
        planner_type: Optional[PlannerType] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseMealPlanner:
        """
        Create a meal planner instance.
        
        Args:
            planner_type: Type of planner to create. If None, auto-detect based on environment.
            config: Configuration dictionary for the planner.
            
        Returns:
            An instance of a BaseMealPlanner implementation.
        """
        config = config or {}
        
        # Auto-detect planner type if not specified
        if planner_type is None:
            planner_type = cls._detect_planner_type()
        
        # Get the planner class
        planner_class = cls._planner_classes.get(planner_type)
        if not planner_class:
            logger.warning(f"Unknown planner type: {planner_type}. Using fallback.")
            planner_class = FallbackMealPlanner
        
        try:
            # Initialize the planner with config
            return planner_class(**config)
        except Exception as e:
            logger.error(f"Failed to initialize {planner_type} planner: {e}")
            logger.info("Falling back to FallbackMealPlanner")
            return FallbackMealPlanner(**config)
    
    @classmethod
    def _detect_planner_type(cls) -> PlannerType:
        """Detect the best available planner based on environment."""
        import os
        
        # Check for OpenAI API key
        if os.getenv('OPENAI_API_KEY'):
            return PlannerType.OPENAI
            
        # Check for Ollama
        try:
            import requests
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any(model['name'].startswith(('llama', 'mistral')) for model in models):
                    return PlannerType.OLLAMA
        except:
            pass
            
        # Check for Hugging Face
        if os.getenv('HUGGINGFACE_API_KEY'):
            return PlannerType.HUGGINGFACE
            
        # Default to fallback
        return PlannerType.FALLBACK
