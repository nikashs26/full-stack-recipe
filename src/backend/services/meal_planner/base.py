from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

@dataclass
class MacroTargets:
    """Macro nutrient targets in grams."""
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 30.0

    def to_dict(self) -> Dict[str, float]:
        return {
            'calories': self.calories,
            'protein_g': self.protein_g,
            'carbs_g': self.carbs_g,
            'fat_g': self.fat_g,
            'fiber_g': self.fiber_g
        }

@dataclass
class Meal:
    """Represents a single meal in the meal plan."""
    id: str
    name: str
    description: str
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    nutrition: Dict[str, float]
    prep_time: int  # in minutes
    cook_time: int  # in minutes
    servings: int = 1
    tags: List[str] = None
    image_url: Optional[str] = None

@dataclass
class DailyMealPlan:
    """Meal plan for a single day."""
    date: str  # ISO format date
    meals: Dict[MealType, Meal]
    nutrition: Dict[str, float]

@dataclass
class WeeklyMealPlan:
    """Weekly meal plan with daily plans and summary."""
    days: Dict[str, DailyMealPlan]  # Key is day name (monday, tuesday, etc.)
    summary: Dict[str, Any]
    preferences: Dict[str, Any]

class BaseMealPlanner(ABC):
    """Base interface for all meal planner implementations."""
    
    @abstractmethod
    def generate_weekly_plan(
        self,
        preferences: Dict[str, Any],
        macro_targets: Optional[MacroTargets] = None
    ) -> WeeklyMealPlan:
        """Generate a weekly meal plan based on preferences and macro targets."""
        pass
    
    @abstractmethod
    def regenerate_meal(
        self,
        day: str,
        meal_type: MealType,
        current_plan: WeeklyMealPlan,
        constraints: Dict[str, Any] = None
    ) -> Meal:
        """Regenerate a specific meal in the plan."""
        pass
    
    @abstractmethod
    def get_recipe_suggestions(
        self,
        meal_type: MealType,
        preferences: Dict[str, Any],
        count: int = 3
    ) -> List[Meal]:
        """Get recipe suggestions for a specific meal type."""
        pass
