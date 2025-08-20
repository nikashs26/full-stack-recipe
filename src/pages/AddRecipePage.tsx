
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import RecipeForm from '../components/RecipeForm';
import { addRecipe } from '../utils/storage';
import { Recipe } from '../types/recipe';
import { useToast } from "@/hooks/use-toast";

const AddRecipePage: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleAddRecipe = (recipeData: Omit<Recipe, 'id' | 'ratings' | 'comments'>) => {
    const newRecipe = addRecipe({
      ...recipeData,
      ratings: [],
      comments: []
    });
    
    toast({
      title: "Recipe created",
      description: "Your new recipe has been added successfully.",
    });
    
    navigate(`/recipes/${newRecipe.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Add New Recipe</h1>
        
        <div className="bg-white shadow-lg rounded-lg p-6 animate-fade-in">
          <RecipeForm onSubmit={handleAddRecipe} />
        </div>
      </main>
    </div>
  );
};

export default AddRecipePage;
