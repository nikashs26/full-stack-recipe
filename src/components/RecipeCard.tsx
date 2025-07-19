
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Edit, Trash2, Star, Clock, Folder, Heart } from 'lucide-react';
import { Recipe } from '../types/recipe';
import { getDietaryTags, getAverageRating, formatExternalRecipeCuisine } from '../utils/recipeUtils';
import { SpoonacularRecipe } from '../types/spoonacular';

interface RecipeCardProps {
  recipe: Recipe;
  isExternal?: boolean;
  onDelete?: (id: string) => void;
}

const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, isExternal = false, onDelete }) => {
  // Handle both name and title fields
  const recipeName = recipe.name || recipe.title || "Untitled Recipe";
  
  // Handle both cuisine formats
  const cuisines = Array.isArray(recipe.cuisines) ? recipe.cuisines : [recipe.cuisine].filter(Boolean);
  
  // Handle both dietary restriction formats
  const dietaryRestrictions = recipe.dietaryRestrictions || recipe.diets || [];
  
  // Handle both image formats
  const imageUrl = recipe.image || recipe.imageUrl || "/placeholder.svg";
  
  // Handle both ID formats
  const recipeId = recipe.id?.toString() || "";
  
  // Handle both ingredient formats
  const ingredients = recipe.ingredients?.map(ing => 
    typeof ing === 'string' ? ing : ing.name
  ) || [];

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      <Link to={isExternal ? `/external-recipe/${recipeId}` : `/recipe/${recipeId}`}>
        <div className="relative h-48 overflow-hidden">
          <img
            src={imageUrl}
            alt={recipeName}
            className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              e.currentTarget.src = "/placeholder.svg";
            }}
          />
        </div>
        
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {recipeName}
          </h3>
          
          {/* Cuisine Tags */}
          {cuisines.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              {cuisines.map((cuisine, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                >
                  {cuisine}
                </span>
              ))}
            </div>
          )}
          
          {/* Dietary Tags */}
          {dietaryRestrictions.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              {dietaryRestrictions.map((diet, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                >
                  {diet}
                </span>
              ))}
            </div>
          )}
          
          {/* Ingredients Preview */}
          {ingredients.length > 0 && (
            <p className="text-sm text-gray-600 line-clamp-2">
              {ingredients.slice(0, 3).join(", ")}
              {ingredients.length > 3 && "..."}
            </p>
          )}
        </div>
      </Link>
      
      {/* Delete Button - Only show for non-external recipes */}
      {!isExternal && onDelete && (
        <div className="p-4 pt-0">
          <button
            onClick={() => onDelete(recipeId)}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Delete Recipe
          </button>
        </div>
      )}
    </div>
  );
};
export default RecipeCard;

