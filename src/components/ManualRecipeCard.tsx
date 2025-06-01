
import React from 'react';
import { Link } from 'react-router-dom';
import { Clock } from 'lucide-react';
import { ManualRecipe } from '../lib/manualRecipes';

interface ManualRecipeCardProps {
  recipe: ManualRecipe;
}

const ManualRecipeCard: React.FC<ManualRecipeCardProps> = ({ recipe }) => {
  const [imageSrc, setImageSrc] = React.useState(recipe.image || '/placeholder.svg');
  
  const handleImageError = () => {
    console.log(`Image error for manual recipe: ${recipe.title}, using placeholder`);
    setImageSrc('/placeholder.svg');
  };

  // Format cuisine for display
  const cuisineDisplay = recipe.cuisine && recipe.cuisine.length > 0 
    ? recipe.cuisine.join(', ') 
    : 'Other';

  // Format diets for display
  const dietsDisplay = recipe.diets && recipe.diets.length > 0 
    ? recipe.diets.map(diet => ({
        text: diet.charAt(0).toUpperCase() + diet.slice(1),
        class: `${diet.toLowerCase()}-tag`
      }))
    : [];

  return (
    <div className="recipe-card animate-scale-in bg-white rounded-lg shadow-md overflow-hidden transition-transform hover:shadow-lg">
      <div className="relative">
        <Link to={`/manual-recipe/${recipe.id}`} className="block">
          <div className="relative h-48 w-full overflow-hidden">
            <img 
              src={imageSrc} 
              alt={recipe.title || "Manual Recipe"} 
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 hover:scale-110"
              onError={handleImageError}
              loading="lazy"
            />
            
            {/* Time badge */}
            {recipe.ready_in_minutes && (
              <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white rounded-full px-2 py-1 text-sm flex items-center">
                <Clock className="h-4 w-4 text-white mr-1" />
                <span>{recipe.ready_in_minutes} min</span>
              </div>
            )}
          </div>
        </Link>
      </div>
      
      <div className="p-5">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 line-clamp-1">
          <Link to={`/manual-recipe/${recipe.id}`} className="hover:text-recipe-primary transition-colors">
            {recipe.title || "Untitled Recipe"}
          </Link>
        </h2>
        <p className="text-sm text-gray-600 mb-2">Cuisine: {cuisineDisplay}</p>
        
        <div className="mb-4">
          {dietsDisplay.map((tag, index) => (
            <span key={index} className={`recipe-tag ${tag.class}`}>
              {tag.text}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ManualRecipeCard;
