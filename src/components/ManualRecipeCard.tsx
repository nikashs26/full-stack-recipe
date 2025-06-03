
import React from 'react';
import { Link } from 'react-router-dom';
import { Clock, ChefHat } from 'lucide-react';
import { Database } from "@/integrations/supabase/types";

type ManualRecipe = Database['public']['Tables']['manual_recipes']['Row'];

interface ManualRecipeCardProps {
  recipe: ManualRecipe;
}

const ManualRecipeCard: React.FC<ManualRecipeCardProps> = ({ recipe }) => {
  return (
    <Link 
      to={`/manual-recipe/${recipe.id}`}
      className="block bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden"
    >
      <div className="relative">
        <img
          src={recipe.image || '/placeholder.svg'}
          alt={recipe.title}
          className="w-full h-48 object-cover"
        />
        <div className="absolute top-2 right-2">
          <div className="bg-blue-500 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
            <ChefHat className="h-3 w-3" />
            Manual
          </div>
        </div>
      </div>
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {recipe.title}
        </h3>
        
        <div className="flex flex-wrap gap-2 mb-3">
          {recipe.cuisine && recipe.cuisine.map((cuisine, index) => (
            <span 
              key={index}
              className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full"
            >
              {cuisine}
            </span>
          ))}
        </div>
        
        <div className="flex flex-wrap gap-2 mb-3">
          {recipe.diets && recipe.diets.map((diet, index) => (
            <span 
              key={index}
              className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
            >
              {diet}
            </span>
          ))}
        </div>
        
        {recipe.ready_in_minutes && (
          <div className="flex items-center text-gray-600 text-sm">
            <Clock className="h-4 w-4 mr-1" />
            {recipe.ready_in_minutes} minutes
          </div>
        )}
        
        {recipe.description && (
          <p className="text-gray-600 text-sm mt-2 line-clamp-2">
            {recipe.description}
          </p>
        )}
      </div>
    </Link>
  );
};

export default ManualRecipeCard;
