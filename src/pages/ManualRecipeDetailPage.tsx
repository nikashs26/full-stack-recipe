
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Clock, Users, ChefHat } from 'lucide-react';
import Header from '../components/Header';
import { fetchManualRecipes } from '../lib/manualRecipes';

const ManualRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  
  const { data: manualRecipes = [], isLoading, error } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: fetchManualRecipes,
  });

  const recipe = manualRecipes.find(r => r.id === parseInt(id || '0'));

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center items-center py-12">
          <div className="text-gray-600">Loading recipe...</div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Recipe Not Found</h1>
            <p className="text-gray-600 mb-4">The recipe you're looking for doesn't exist.</p>
            <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
              ← Back to Recipes
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link 
          to="/recipes" 
          className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6"
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Recipes
        </Link>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="relative h-64 md:h-80">
            <img 
              src={recipe.image || '/placeholder.svg'} 
              alt={recipe.title} 
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder.svg';
              }}
            />
          </div>

          <div className="p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{recipe.title}</h1>
            
            <div className="flex flex-wrap gap-4 mb-6">
              {recipe.ready_in_minutes && (
                <div className="flex items-center text-gray-600">
                  <Clock className="mr-2 h-5 w-5" />
                  <span>{recipe.ready_in_minutes} minutes</span>
                </div>
              )}
              
              {recipe.cuisine && recipe.cuisine.length > 0 && (
                <div className="flex items-center text-gray-600">
                  <ChefHat className="mr-2 h-5 w-5" />
                  <span>{recipe.cuisine.join(', ')}</span>
                </div>
              )}
            </div>

            {recipe.diets && recipe.diets.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Dietary Information</h3>
                <div className="flex flex-wrap gap-2">
                  {recipe.diets.map((diet, index) => (
                    <span 
                      key={index} 
                      className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                    >
                      {diet.charAt(0).toUpperCase() + diet.slice(1)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="text-center py-8 text-gray-500">
              <p>This is a manually added recipe. More details can be added by editing the database.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManualRecipeDetailPage;
