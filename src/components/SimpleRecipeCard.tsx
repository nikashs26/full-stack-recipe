import React from 'react';
import { Clock, Star } from 'lucide-react';

interface SimpleRecipe {
  id: string;
  name?: string;
  title?: string;
  image?: string;
  cookingTime?: string;
  cuisine?: string;
  difficulty?: string;
}

interface SimpleRecipeCardProps {
  recipe: SimpleRecipe;
}

const SimpleRecipeCard: React.FC<SimpleRecipeCardProps> = ({ recipe }) => {
  const recipeName = recipe.name || recipe.title || "Untitled Recipe";
  
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 h-full flex flex-col">
      <div className="relative h-48 overflow-hidden">
        <img
          src={recipe.image || "/placeholder.svg"}
          alt={recipeName}
          className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-300"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            if (target.src !== "/placeholder.svg") {
              target.src = "/placeholder.svg";
            }
          }}
        />
      </div>
      
      <div className="p-4 flex-grow">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {recipeName}
        </h3>
        
        {recipe.cuisine && (
          <span className="px-2.5 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
            🌎 {recipe.cuisine}
          </span>
        )}
        
        <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center">
            <Clock className="w-4 h-4 mr-1" />
            <span>{recipe.cookingTime || 'N/A'}</span>
          </div>
          <div className="flex items-center">
            <Star className="w-4 h-4 text-yellow-400 mr-1" />
            <span>4.5</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleRecipeCard;