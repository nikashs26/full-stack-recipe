
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, Star, Clock, Folder, Heart } from 'lucide-react';
import { Recipe } from '../types/recipe';
import { getDietaryTags, getAverageRating, formatExternalRecipeCuisine } from '../utils/recipeUtils';
import { SpoonacularRecipe } from '../types/spoonacular';

interface RecipeCardProps {
  recipe: Recipe | SpoonacularRecipe;
  onDelete: (id: string) => void;
  onToggleFavorite?: (recipe: Recipe) => void;
  isExternal?: boolean;
  folderName?: string;
}

const RecipeCard: React.FC<RecipeCardProps> = ({ 
  recipe, 
  onDelete, 
  onToggleFavorite,
  isExternal = false,
  folderName
}) => {
  // Safety check for null/undefined recipe
  if (!recipe) {
    console.error("Received null or undefined recipe in RecipeCard");
    return null;
  }

  // Handle both local and external recipe types with proper null checks
  const recipeId = isExternal 
    ? String((recipe as SpoonacularRecipe).id || "unknown") 
    : (recipe as Recipe).id || "unknown";
  
  const recipeName = isExternal 
    ? (recipe as SpoonacularRecipe).title || "Untitled Recipe" 
    : (recipe as Recipe).name || "Untitled Recipe";
  
  // Updated cuisine handling with null checks
  const recipeCuisine = isExternal 
    ? formatExternalRecipeCuisine(recipe as SpoonacularRecipe)
    : (recipe as Recipe).cuisine || "Other";
  
  const recipeImage = isExternal 
    ? (recipe as SpoonacularRecipe).image || '/placeholder.svg' 
    : (recipe as Recipe).image || '/placeholder.svg';
  
  // ALWAYS show external theme - time badge and consistent styling
  const readyInMinutes = isExternal 
    ? (recipe as SpoonacularRecipe).readyInMinutes || 30
    : 30; // Default time for all recipes
  
  // Favorite status (only applies to local recipes)
  const isFavorite = !isExternal && (recipe as Recipe).isFavorite;
  
  // Improved dietary tags mapping for all recipes
  let dietaryTags = [];
  
  if (isExternal) {
    const diets = ((recipe as SpoonacularRecipe).diets || []);
    const mappedDiets = diets
      .filter(diet => diet && typeof diet === 'string')
      .map(diet => {
        const dietLower = diet.toLowerCase();
        if (dietLower.includes('vegetarian') && !dietLower.includes('lacto') && !dietLower.includes('ovo')) return 'vegetarian';
        if (dietLower.includes('vegan')) return 'vegan'; 
        if (dietLower.includes('gluten') && dietLower.includes('free')) return 'gluten-free';
        return null;
      })
      .filter(diet => diet !== null);
    
    dietaryTags = getDietaryTags(mappedDiets as any);
  } else {
    dietaryTags = getDietaryTags((recipe as Recipe).dietaryRestrictions || []);
  }
  
  // Fallback image handling
  const [imageSrc, setImageSrc] = React.useState(recipeImage || '/placeholder.svg');
  
  // Handle image loading errors
  const handleImageError = () => {
    console.log(`Image error for recipe: ${recipeName}, using placeholder`);
    setImageSrc('/placeholder.svg');
  };

  // Fixed the link path logic - external vs manual vs local recipes
  let cardLink = '';
  if (isExternal) {
    cardLink = `/external-recipe/${recipeId}`;
  } else {
    // Check if it's a manual recipe by looking at the recipe structure
    const isManualRecipe = (recipe as any).cooking_instructions !== undefined || 
                          (recipe as any).description !== undefined ||
                          (recipe as any).ready_in_minutes !== undefined;
    
    if (isManualRecipe) {
      cardLink = `/manual-recipe/${recipeId}`;
    } else {
      cardLink = `/recipe/${recipeId}`;
    }
  }

  // Handle favorite toggle
  const handleToggleFavorite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isExternal && onToggleFavorite) {
      onToggleFavorite(recipe as Recipe);
    }
  };

  return (
    <div className="recipe-card animate-scale-in bg-white rounded-lg shadow-md overflow-hidden transition-transform hover:shadow-lg">
      <div className="relative">
        <Link to={cardLink} className="block">
          <div className="relative h-48 w-full overflow-hidden">
            <img 
              src={imageSrc} 
              alt={recipeName || "Recipe"} 
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 hover:scale-110"
              onError={handleImageError}
              loading="lazy"
            />
            
            {/* ALWAYS show time badge for consistent external theming */}
            <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white rounded-full px-2 py-1 text-sm flex items-center">
              <Clock className="h-4 w-4 text-white mr-1" />
              <span>{readyInMinutes} min</span>
            </div>
          </div>
        </Link>
        
        {/* Favorite button */}
        {!isExternal && onToggleFavorite && (
          <button
            onClick={handleToggleFavorite}
            className={`absolute top-2 left-2 p-1 rounded-full ${isFavorite ? 'text-red-500' : 'text-white bg-black bg-opacity-40'}`}
          >
            <Heart 
              className="h-5 w-5" 
              fill={isFavorite ? "currentColor" : "none"} 
            />
          </button>
        )}
      </div>
      
      <div className="p-5">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 line-clamp-1">
          <Link to={cardLink} className="hover:text-recipe-primary transition-colors">
            {recipeName || "Untitled Recipe"}
          </Link>
        </h2>
        <p className="text-sm text-gray-600 mb-2">Cuisine: {recipeCuisine || "Other"}</p>
        
        {folderName && (
          <div className="mb-2 text-xs flex items-center text-gray-500">
            <Folder className="h-3 w-3 mr-1" />
            <span>{folderName}</span>
          </div>
        )}
        
        <div className="mb-4">
          {/* Show dietary tags only if they exist and are properly mapped */}
          {dietaryTags && dietaryTags.length > 0 && dietaryTags.map((tag, index) => (
            <span key={index} className={`recipe-tag ${tag.class}`}>
              {tag.text}
            </span>
          ))}
        </div>
        
        {!isExternal && (
          <div className="flex justify-between items-center">
            <Link 
              to={`/edit-recipe/${recipeId}`} 
              className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 transition-colors"
            >
              <Edit className="mr-1 h-4 w-4" /> Edit
            </Link>
            <button 
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (recipeId && recipeId !== "unknown") {
                  onDelete(recipeId);
                }
              }}
              className="inline-flex items-center text-red-600 hover:text-red-800 transition-colors"
            >
              <Trash2 className="mr-1 h-4 w-4" /> Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
export default RecipeCard;

