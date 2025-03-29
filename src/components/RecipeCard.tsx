
import React from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, Star, ExternalLink } from 'lucide-react';
import { Recipe } from '../types/recipe';
import { getDietaryTags, getAverageRating } from '../utils/recipeUtils';

interface RecipeCardProps {
  recipe: Recipe;
  onDelete: (id: string) => void;
  isExternal?: boolean;
}

const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, onDelete, isExternal = false }) => {
  const dietaryTags = getDietaryTags(recipe.dietaryRestrictions);
  const avgRating = getAverageRating(recipe.ratings);
  
  // Fallback image if recipe image is missing
  const [imageSrc, setImageSrc] = React.useState(recipe.image || '/placeholder.svg');

  // Handle image loading errors
  const handleImageError = () => {
    console.log(`Image error for recipe: ${recipe.name}, using placeholder`);
    setImageSrc('/placeholder.svg');
  };

  return (
    <div className="recipe-card animate-scale-in bg-white rounded-lg shadow-md overflow-hidden transition-transform hover:shadow-lg">
      {isExternal ? (
        // External recipes don't have detail pages
        <div className="relative h-48 w-full overflow-hidden">
          <img 
            src={imageSrc} 
            alt={recipe.name} 
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 hover:scale-110"
            onError={handleImageError}
          />
          {recipe.ratings.length > 0 && (
            <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white rounded-full px-2 py-1 text-sm flex items-center">
              <Star className="h-4 w-4 text-yellow-400 mr-1" />
              <span>{avgRating}</span>
            </div>
          )}
          <div className="absolute top-2 left-2 bg-blue-500 bg-opacity-80 text-white rounded-full px-2 py-1 text-xs">
            External
          </div>
        </div>
      ) : (
        // Internal recipes have detail pages
        <Link to={`/recipe/${recipe.id}`} className="block">
          <div className="relative h-48 w-full overflow-hidden">
            <img 
              src={imageSrc} 
              alt={recipe.name} 
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 hover:scale-110"
              onError={handleImageError}
            />
            {recipe.ratings.length > 0 && (
              <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white rounded-full px-2 py-1 text-sm flex items-center">
                <Star className="h-4 w-4 text-yellow-400 mr-1" />
                <span>{avgRating}</span>
              </div>
            )}
          </div>
        </Link>
      )}
      
      <div className="p-5">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 line-clamp-1">
          {isExternal ? (
            <span className="flex items-center">
              {recipe.name}
              <ExternalLink className="h-4 w-4 ml-1 text-blue-500" />
            </span>
          ) : (
            <Link to={`/recipe/${recipe.id}`} className="hover:text-recipe-primary transition-colors">
              {recipe.name}
            </Link>
          )}
        </h2>
        <p className="text-sm text-gray-600 mb-2">Cuisine: {recipe.cuisine}</p>
        
        <div className="mb-4">
          {dietaryTags.map((tag, index) => (
            <span key={index} className={`recipe-tag ${tag.class}`}>
              {tag.text}
            </span>
          ))}
        </div>
        
        {!isExternal && (
          <div className="flex justify-between items-center">
            <Link 
              to={`/edit-recipe/${recipe.id}`} 
              className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 transition-colors"
            >
              <Edit className="mr-1 h-4 w-4" /> Edit
            </Link>
            <button 
              onClick={() => onDelete(recipe.id)}
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
