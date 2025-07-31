
import React from 'react';
import { Link } from 'react-router-dom';
import { ManualRecipe } from '../types/manualRecipe';
import { ChefHat, Clock } from 'lucide-react';
import { getDietaryTags } from '../utils/recipeUtils';
import { DietaryRestriction } from '../types/recipe';

interface ManualRecipeCardProps {
  recipe: ManualRecipe;
}

const ManualRecipeCard: React.FC<ManualRecipeCardProps> = ({ recipe }) => {
  // Enhanced title handling to ensure no untitled recipes
  const displayTitle = (() => {
    let title = recipe.title || "";
    
    // Fix untitled recipes with enhanced logic
    if (!title || title.toLowerCase().includes("untitled") || title.trim() === "") {
      // Strategy 1: Use cuisine
      if (recipe.cuisine && recipe.cuisine.length > 0) {
        const mainCuisine = recipe.cuisine[0];
        title = `Authentic ${mainCuisine} Recipe`;
      } 
      // Strategy 2: Use ID-based fallback
      else {
        const recipeId = recipe.id || Math.random().toString(36).substr(2, 9);
        title = `Home Kitchen Recipe #${recipeId}`;
      }
    }
    return title;
  })();

  // Map diet strings to proper dietary restriction enum values
  const mappedDiets = (recipe.diets || [])
    .filter((diet): diet is string => Boolean(diet) && typeof diet === 'string')
    .map(diet => {
      const dietLower = diet.toLowerCase();
      // Map common diet names to our standard format
      if (dietLower.includes('vegetarian')) return DietaryRestriction.VEGETARIAN;
      if (dietLower.includes('vegan')) return DietaryRestriction.VEGAN;
      if (dietLower.includes('gluten') && dietLower.includes('free')) return DietaryRestriction.GLUTEN_FREE;
      if (dietLower.includes('dairy') && dietLower.includes('free')) return DietaryRestriction.DAIRY_FREE;
      if (dietLower.includes('ketogenic') || dietLower.includes('keto')) return DietaryRestriction.KETO;
      if (dietLower.includes('paleo')) return DietaryRestriction.PALEO;
      if (dietLower.includes('nut') && dietLower.includes('free')) return DietaryRestriction.NUT_FREE;
      if (dietLower.includes('low') && dietLower.includes('carb')) return DietaryRestriction.LOW_CARB;
      if (dietLower.includes('low') && dietLower.includes('calorie')) return DietaryRestriction.LOW_CALORIE;
      if (dietLower.includes('low') && dietLower.includes('sodium')) return DietaryRestriction.LOW_SODIUM;
      if (dietLower.includes('high') && dietLower.includes('protein')) return DietaryRestriction.HIGH_PROTEIN;
      if (dietLower.includes('pescetarian')) return DietaryRestriction.PESCETARIAN;
      return diet as DietaryRestriction;
    })
    .filter((diet): diet is DietaryRestriction => 
      Object.values(DietaryRestriction).includes(diet as DietaryRestriction)
    );
  
  const dietaryTags = getDietaryTags(mappedDiets);

  // Enhanced cuisine display with proper type checking
  const displayCuisines = (() => {
    if (!recipe.cuisine) return ["International"];
    // Handle case where cuisine might be a single string
    if (typeof recipe.cuisine === 'string') return [recipe.cuisine];
    // Ensure it's an array
    const cuisines = Array.isArray(recipe.cuisine) ? recipe.cuisine : [];
    return cuisines.length > 0 ? cuisines.slice(0, 2) : ["International"];
  })();

  return (
    <Link 
      to={`/manual-recipe/${recipe.id}`}
      className="recipe-card block transition-all duration-300 hover:shadow-xl"
    >
      <div className="relative">
        <img
          src={recipe.image || '/placeholder.svg'}
          alt={displayTitle}
          className="w-full h-48 object-cover rounded-t-lg"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/placeholder.svg';
          }}
        />
        <div className="absolute top-3 right-3">
          <div className="bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 shadow-md">
            <ChefHat className="h-3 w-3" />
            Manual
          </div>
        </div>
      </div>
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {displayTitle}
        </h3>
        
        {recipe.description && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {recipe.description}
          </p>
        )}
        
        <div className="flex flex-wrap gap-2 mb-3">
          {displayCuisines.map((cuisine, index) => (
            <span 
              key={index}
              className="recipe-tag bg-orange-100 text-orange-800"
            >
              {cuisine}
            </span>
          ))}
        </div>
        
        <div className="mb-3">
          {/* Enhanced dietary tags using our standard format */}
          {dietaryTags && dietaryTags.length > 0 && dietaryTags.map((tag, index) => (
            <span key={index} className={`recipe-tag ${tag.class}`}>
              {tag.text}
            </span>
          ))}
        </div>
        
        {recipe.ready_in_minutes && (
          <div className="flex items-center text-gray-600 text-sm">
            <Clock className="h-4 w-4 mr-1" />
            {recipe.ready_in_minutes} minutes
          </div>
        )}
      </div>
    </Link>
  );
};

export default ManualRecipeCard;
