
import React from 'react';
import { Link } from 'react-router-dom';
import { Recipe } from '../types/recipe';
import { ChefHat, Clock } from 'lucide-react';
import { getDietaryTags } from '../utils/recipeUtils';
import { DietaryRestriction } from '../types/recipe';

interface ManualRecipeCardProps {
  recipe: Recipe;
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
    // First try to get cuisines from the cuisines field
    if (recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
      return recipe.cuisines.slice(0, 2);
    }
    
    // Then try the cuisine field (which can be string[] or string in ManualRecipe)
    if (recipe.cuisine) {
      if (Array.isArray(recipe.cuisine) && recipe.cuisine.length > 0) {
        return recipe.cuisine.slice(0, 2);
      } else if (typeof recipe.cuisine === 'string' && recipe.cuisine.trim()) {
        return [recipe.cuisine.trim()];
      }
    }
    
    // If no cuisine found, return empty array instead of ["International"]
    return [];
  })();

  // Get all available tags for display
  const getAllTags = (() => {
    const allTags: string[] = [];
    
    // Add cuisine tags
    allTags.push(...displayCuisines);
    
    // Add diet tags
    if (recipe.diets) {
      if (Array.isArray(recipe.diets)) {
        allTags.push(...recipe.diets);
      } else if (typeof recipe.diets === 'string') {
        allTags.push(recipe.diets);
      }
    }
    
    // Add dietary restrictions (camelCase from Recipe interface)
    if (recipe.dietaryRestrictions && Array.isArray(recipe.dietaryRestrictions)) {
      allTags.push(...recipe.dietaryRestrictions);
    }
    
    // Add general tags
    if (recipe.tags) {
      if (Array.isArray(recipe.tags)) {
        allTags.push(...recipe.tags);
      } else if (typeof recipe.tags === 'string') {
        allTags.push(recipe.tags);
      }
    }
    
    // Add dish types
    if (recipe.dish_types) {
      if (Array.isArray(recipe.dish_types)) {
        allTags.push(...recipe.dish_types);
      } else if (typeof recipe.dish_types === 'string') {
        allTags.push(recipe.dish_types);
      }
    }
    
    // Remove duplicates and filter out empty strings
    return [...new Set(allTags)].filter(tag => tag && tag.trim()).slice(0, 6); // Limit to 6 tags
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
        
        {/* Display all available tags */}
        {getAllTags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {getAllTags.map((tag, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
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
