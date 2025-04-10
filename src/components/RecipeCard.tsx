
import React from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, Star, Clock } from 'lucide-react';
import { Recipe } from '../types/recipe';
import { getDietaryTags, getAverageRating, formatExternalRecipeCuisine } from '../utils/recipeUtils';
import { SpoonacularRecipe } from '../types/spoonacular';

interface RecipeCardProps {
  recipe: Recipe | SpoonacularRecipe;
  onDelete: (id: string) => void;
  isExternal?: boolean;
}

const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, onDelete, isExternal = false }) => {
  // Handle both local and external recipe types
  const recipeId = isExternal ? (recipe as SpoonacularRecipe).id.toString() : (recipe as Recipe).id;
  const recipeName = isExternal ? (recipe as SpoonacularRecipe).title : (recipe as Recipe).name;
  
  // Updated cuisine handling
  const recipeCuisine = isExternal 
    ? formatExternalRecipeCuisine(recipe as SpoonacularRecipe)
    : (recipe as Recipe).cuisine;
  
  const recipeImage = isExternal 
    ? (recipe as SpoonacularRecipe).image 
    : (recipe as Recipe).image || '/placeholder.svg';
  
  // Ratings handling
  const avgRating = isExternal 
    ? 0 // External recipes don't have ratings
    : getAverageRating((recipe as Recipe).ratings);
  
  // Dietary tags - normalize diets for external recipes to match local format
  let dietaryTags = isExternal 
    ? getDietaryTags(((recipe as SpoonacularRecipe).diets || []).map(diet => {
        // Normalize diet names to match our internal format
        if (diet.toLowerCase().includes('vegetarian')) return 'vegetarian';
        if (diet.toLowerCase().includes('vegan')) return 'vegan'; 
        if (diet.toLowerCase().includes('gluten') && diet.toLowerCase().includes('free')) return 'gluten-free';
        if (diet.toLowerCase().includes('carnivore') || diet.toLowerCase().includes('meat')) return 'carnivore';
        return diet as any;
      }))
    : getDietaryTags((recipe as Recipe).dietaryRestrictions);
  
  // Ready in minutes for external recipes
  const readyInMinutes = isExternal 
    ? (recipe as SpoonacularRecipe).readyInMinutes 
    : undefined;
  
  // Fallback image handling
  const [imageSrc, setImageSrc] = React.useState(recipeImage);
  
  // Handle image loading errors
  const handleImageError = () => {
    console.log(`Image error for recipe: ${recipeName}, using placeholder`);
    setImageSrc('/placeholder.svg');
  };

  // Fix the link path for external recipes
  const cardLink = isExternal 
    ? `/external-recipe/${(recipe as SpoonacularRecipe).id}` 
    : `/recipe/${(recipe as Recipe).id}`;

  return (
    <div className="recipe-card animate-scale-in bg-white rounded-lg shadow-md overflow-hidden transition-transform hover:shadow-lg">
      <Link to={cardLink} className="block">
        <div className="relative h-48 w-full overflow-hidden">
          <img 
            src={imageSrc} 
            alt={recipeName || "Recipe"} 
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 hover:scale-110"
            onError={handleImageError}
            loading="lazy"
          />
          
          {/* Rating badge for local recipes */}
          {!isExternal && (recipe as Recipe).ratings && (recipe as Recipe).ratings.length > 0 && (
            <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white rounded-full px-2 py-1 text-sm flex items-center">
              <Star className="h-4 w-4 text-yellow-400 mr-1" />
              <span>{avgRating}</span>
            </div>
          )}
          
          {/* Time badge for external recipes */}
          {isExternal && readyInMinutes && (
            <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white rounded-full px-2 py-1 text-sm flex items-center">
              <Clock className="h-4 w-4 text-white mr-1" />
              <span>{readyInMinutes} min</span>
            </div>
          )}
        </div>
      </Link>
      
      <div className="p-5">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 line-clamp-1">
          <Link to={cardLink} className="hover:text-recipe-primary transition-colors">
            {recipeName || "Untitled Recipe"}
          </Link>
        </h2>
        <p className="text-sm text-gray-600 mb-2">Cuisine: {recipeCuisine || "Other"}</p>
        
        <div className="mb-4">
          {/* Show dietary tags for both local and external recipes */}
          {dietaryTags && dietaryTags.map((tag, index) => (
            <span key={index} className={`recipe-tag ${tag.class}`}>
              {tag.text}
            </span>
          ))}
        </div>
        
        {!isExternal && (
          <div className="flex justify-between items-center">
            <Link 
              to={`/edit-recipe/${(recipe as Recipe).id}`} 
              className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 transition-colors"
            >
              <Edit className="mr-1 h-4 w-4" /> Edit
            </Link>
            <button 
              onClick={() => onDelete((recipe as Recipe).id)}
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
