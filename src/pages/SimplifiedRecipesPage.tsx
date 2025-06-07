
import React from 'react';
import Header from '../components/Header';
import ManualRecipeCard from '../components/ManualRecipeCard';
import { useManualRecipes } from '../hooks/useManualRecipes';
import { Loader2 } from 'lucide-react';

const SimplifiedRecipesPage: React.FC = () => {
  const { data: manualRecipes = [], isLoading, error } = useManualRecipes();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Recipe Collection</h1>
        </div>
        
        {/* Popular Recipes Section */}
        {isLoading ? (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="ml-2 text-gray-600">Loading popular recipes...</span>
            </div>
          </div>
        ) : error ? (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="text-center py-8">
              <p className="text-red-600">Error loading recipes: {error.message}</p>
            </div>
          </div>
        ) : manualRecipes.length > 0 ? (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {manualRecipes.map((recipe) => (
                <ManualRecipeCard 
                  key={recipe.id}
                  recipe={recipe}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="text-center py-8">
              <p className="text-gray-600">No recipes available yet.</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default SimplifiedRecipesPage;
