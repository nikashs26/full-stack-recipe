
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import RecipeForm from '../components/RecipeForm';
import { getRecipeById, updateRecipe } from '../utils/storage';
import { Recipe } from '../types/recipe';
import { useToast } from "@/hooks/use-toast";

const EditRecipePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    if (id) {
      const foundRecipe = getRecipeById(id);
      if (foundRecipe) {
        setRecipe(foundRecipe);
      }
      setLoading(false);
    }
  }, [id]);

  const handleUpdateRecipe = (recipeData: Omit<Recipe, 'ratings' | 'comments'> & { id?: string }) => {
    if (recipe && recipeData.id) {
      const updatedRecipe: Recipe = {
        ...recipeData,
        id: recipeData.id,
        ratings: recipe.ratings,
        comments: recipe.comments
      };
      
      updateRecipe(updatedRecipe);
      
      toast({
        title: "Recipe updated",
        description: "Your recipe has been updated successfully.",
      });
      
      navigate(`/recipe/${recipe.id}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </main>
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <h2 className="text-2xl font-medium text-gray-600">Recipe Not Found</h2>
            <p className="text-gray-500 mt-2">The recipe you're trying to edit doesn't exist.</p>
            <button 
              onClick={() => navigate('/')} 
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90"
            >
              Go back to all recipes
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Edit Recipe</h1>
        
        <div className="bg-white shadow-lg rounded-lg p-6 animate-fade-in">
          <RecipeForm 
            initialData={recipe}
            onSubmit={handleUpdateRecipe}
            isEdit
          />
        </div>
      </main>
    </div>
  );
};

export default EditRecipePage;
