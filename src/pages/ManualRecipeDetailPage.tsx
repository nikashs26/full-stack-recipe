
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Clock, ChefHat } from 'lucide-react';
import Header from '../components/Header';
import { fetchManualRecipeById } from '../lib/manualRecipes';

const ManualRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['manual-recipe', id],
    queryFn: () => fetchManualRecipeById(parseInt(id!)),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Recipe Not Found</h1>
            <Link 
              to="/recipes" 
              className="text-primary hover:underline"
            >
              Back to Recipes
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
        <div className="mb-6">
          <Link 
            to="/recipes"
            className="inline-flex items-center text-primary hover:underline mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Recipes
          </Link>
          
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="relative">
              <img
                src={recipe.image || '/placeholder.svg'}
                alt={recipe.title}
                className="w-full h-64 sm:h-80 object-cover"
              />
              <div className="absolute top-4 right-4">
                <div className="bg-blue-500 text-white px-3 py-2 rounded-full text-sm font-medium flex items-center gap-2">
                  <ChefHat className="h-4 w-4" />
                  Manual Recipe
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{recipe.title}</h1>
              
              <div className="flex flex-wrap gap-4 mb-6">
                {recipe.ready_in_minutes && (
                  <div className="flex items-center text-gray-600">
                    <Clock className="h-5 w-5 mr-2" />
                    <span>{recipe.ready_in_minutes} minutes</span>
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {recipe.cuisine && recipe.cuisine.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Cuisine</h3>
                    <div className="flex flex-wrap gap-2">
                      {recipe.cuisine.map((cuisine, index) => (
                        <span 
                          key={index}
                          className="px-3 py-1 bg-orange-100 text-orange-800 text-sm rounded-full"
                        >
                          {cuisine}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {recipe.diets && recipe.diets.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Dietary Restrictions</h3>
                    <div className="flex flex-wrap gap-2">
                      {recipe.diets.map((diet, index) => (
                        <span 
                          key={index}
                          className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full"
                        >
                          {diet}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              {recipe.description && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-700 leading-relaxed">{recipe.description}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManualRecipeDetailPage;
