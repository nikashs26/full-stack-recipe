
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

  // Debug logging
  console.log("RecipeCard received recipe:", {
    id: recipe.id,
    title: (recipe as any).title,
    name: (recipe as any).name,
    isExternal,
    type: typeof recipe
  });

  // Handle both local and external recipe types with proper null checks
  const recipeId = isExternal 
    ? String((recipe as SpoonacularRecipe).id || "unknown") 
    : (recipe as Recipe).id || "unknown";
  
  // Enhanced recipe name handling to fix "untitled recipe" issue
  const recipeName = (() => {
    if (isExternal) {
      const spoonacularRecipe = recipe as SpoonacularRecipe;
      let title = spoonacularRecipe.title || "";
      
      // Fix untitled recipes with enhanced logic
      if (!title || title.toLowerCase().includes("untitled") || title.trim() === "") {
        // Strategy 1: Use cuisines + dish types
        if (spoonacularRecipe.cuisines && spoonacularRecipe.cuisines.length > 0) {
          const cuisine = spoonacularRecipe.cuisines[0];
          if (spoonacularRecipe.dishTypes && spoonacularRecipe.dishTypes.length > 0) {
            const dishType = spoonacularRecipe.dishTypes[0];
            title = `${cuisine} ${dishType}`;
          } else {
            title = `Traditional ${cuisine} Recipe`;
          }
        } 
        // Strategy 2: Use main ingredient
        else if (spoonacularRecipe.extendedIngredients && spoonacularRecipe.extendedIngredients.length > 0) {
          const mainIngredient = spoonacularRecipe.extendedIngredients[0].name || "Special";
          const formatted = mainIngredient.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join(' ');
          title = `Homestyle ${formatted}`;
        } 
        // Strategy 3: Appealing fallback
        else {
          const recipeId = spoonacularRecipe.id || Math.random().toString(36).substr(2, 9);
          title = `Chef's Special Recipe #${recipeId}`;
        }
      }
      return title;
    } else {
      const localRecipe = recipe as Recipe;
      let name = localRecipe.name || "";
      
      // Fix untitled local recipes with enhanced logic
      if (!name || name.toLowerCase().includes("untitled") || name.trim() === "") {
        // Strategy 1: Use cuisine
        if (localRecipe.cuisine && localRecipe.cuisine !== "Other") {
          name = `Classic ${localRecipe.cuisine} Recipe`;
        } 
        // Strategy 2: Use main ingredient
        else if (localRecipe.ingredients && localRecipe.ingredients.length > 0) {
          const mainIngredient = localRecipe.ingredients[0] || "Special";
          const formatted = mainIngredient.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join(' ');
          name = `Home Kitchen ${formatted}`;
        } 
        // Strategy 3: Use ID or appealing fallback
        else {
          const recipeId = localRecipe.id || Math.random().toString(36).substr(2, 9);
          name = `Family Recipe #${recipeId}`;
        }
      }
      return name;
    }
  })();
  
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
  
  // Enhanced dietary tags mapping for all recipes
  let dietaryTags = [];
  
  if (isExternal) {
    const diets = ((recipe as SpoonacularRecipe).diets || []);
    const mappedDiets = diets
      .filter(diet => diet && typeof diet === 'string')
      .map(diet => {
        const dietLower = diet.toLowerCase();
        // Map Spoonacular diet names to our standard format
        if (dietLower.includes('vegetarian') && !dietLower.includes('lacto') && !dietLower.includes('ovo')) return 'vegetarian';
        if (dietLower.includes('vegan')) return 'vegan'; 
        if (dietLower.includes('gluten') && dietLower.includes('free')) return 'gluten-free';
        if (dietLower.includes('dairy') && dietLower.includes('free')) return 'dairy-free';
        if (dietLower.includes('ketogenic') || dietLower.includes('keto')) return 'keto';
        if (dietLower.includes('paleo') || dietLower.includes('paleolithic')) return 'paleo';
        if (dietLower.includes('carnivore')) return 'carnivore';
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

  const navigate = useNavigate();

  const handleClick = () => {
    console.log('🔍 RecipeCard click - Recipe data:', { recipe, recipeId, recipeType: (recipe as any).type });
    
    let cardLink;
    
    // Get the recipe type from the recipe object itself or context
    const recipeType = (recipe as any).type;
    
    // Check if this is explicitly marked as a specific type
    if (recipeType === 'manual') {
      cardLink = `/manual-recipe/${recipeId}`;
    } else if (recipeType === 'local' || recipeType === 'saved') {
      cardLink = `/recipe/${recipeId}`;
    } else if (recipeType === 'external') {
      cardLink = `/external-recipe/${recipeId}`;
    } else {
      // Auto-detect based on recipe structure and ID format
      // Recipes from /recipes endpoint (fallback recipes) have Spoonacular-like structure
      const hasSpoonacularStructure = (
        (recipe as any).title && 
        (recipe as any).cuisines && 
        (recipe as any).extendedIngredients &&
        (recipe as any).readyInMinutes !== undefined
      );
      
      // Manual recipes have specific properties
      const isManualRecipe = (
        (recipe as any).ready_in_minutes !== undefined ||
        (recipe as any).description !== undefined ||
        (recipe as any).created_at !== undefined ||
        (recipe as any).updated_at !== undefined ||
        (typeof recipeId === 'string' && (
          recipeId.includes('sample_') ||
          recipeId.includes('manual_') ||
          recipeId.includes('_')
        ))
      );
      
      // Local recipes from storage have specific Recipe interface properties
      const isLocalRecipe = (
        (recipe as any).ratings !== undefined ||
        (recipe as any).comments !== undefined ||
        (recipe as any).folderId !== undefined ||
        (recipe as any).isFavorite !== undefined
      );
      
      // Route based on detected type
      if (isLocalRecipe) {
        cardLink = `/recipe/${recipeId}`;
      } else if (isManualRecipe && !hasSpoonacularStructure) {
        cardLink = `/manual-recipe/${recipeId}`;
      } else if (hasSpoonacularStructure || recipeType === 'spoonacular') {
        // Backend fallback recipes and Spoonacular recipes → external route
        cardLink = `/external-recipe/${recipeId}`;
      } else {
        // Fallback: numeric ID → external, others → manual
        if (typeof recipeId === 'number' || /^\d+$/.test(String(recipeId))) {
          cardLink = `/external-recipe/${recipeId}`;
        } else {
          cardLink = `/manual-recipe/${recipeId}`;
        }
      }
    }

    console.log('🚀 RecipeCard navigating to:', cardLink);
    navigate(cardLink);
  };

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
        <div onClick={handleClick} className="block cursor-pointer">
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
        </div>
        
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
          <span onClick={handleClick} className="hover:text-recipe-primary transition-colors cursor-pointer">
            {recipeName || "Untitled Recipe"}
          </span>
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

