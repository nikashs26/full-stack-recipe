
import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '../components/Header';
import RecipeCard from '../components/RecipeCard';
import { loadRecipes, updateRecipe } from '../utils/storage';
import { Recipe } from '../types/recipe';
import { Heart } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const FavoritesPage: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Fetch recipes
  const { data: recipes = [] } = useQuery({
    queryKey: ['recipes'],
    queryFn: loadRecipes
  });
  
  // Filter favorites
  const favoriteRecipes = recipes.filter((recipe: Recipe) => recipe.isFavorite);



  const handleToggleFavorite = (recipe: Recipe) => {
    const updatedRecipe = {
      ...recipe,
      isFavorite: false
    };
    updateRecipe(updatedRecipe);
    
    // Update query cache data directly without invalidating (prevents refresh)
    queryClient.setQueryData(['recipes'], (oldData: Recipe[]) => {
      if (!oldData) return oldData;
      return oldData.map(r => r.id === updatedRecipe.id ? updatedRecipe : r);
    });
    
    toast({
      title: "Removed from favorites",
      description: `"${recipe.name}" has been removed from your favorites.`,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="pt-24 md:pt-28">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center mb-8 gap-2">
            <Heart className="text-red-500 h-6 w-6" fill="currentColor" />
            <h1 className="text-3xl font-bold">My Favorite Recipes</h1>
          </div>

          {favoriteRecipes.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {favoriteRecipes.map((recipe: Recipe) => (
                <RecipeCard 
                  key={recipe.id}
                  recipe={recipe}
                  onToggleFavorite={handleToggleFavorite}
                  isExternal={false}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Heart className="mx-auto h-12 w-12 text-gray-400" strokeWidth={1.5} />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No favorite recipes yet</h3>
              <p className="mt-1 text-gray-500">
                Mark recipes as favorites to see them here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FavoritesPage;
