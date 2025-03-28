
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Edit, ArrowLeft, Star, Trash2 } from 'lucide-react';
import Header from '../components/Header';
import { getRecipeById, deleteRecipe } from '../utils/storage';
import { getDietaryTags, getAverageRating } from '../utils/recipeUtils';
import { Recipe } from '../types/recipe';
import { useToast } from "@/hooks/use-toast";

const RecipeDetailPage: React.FC = () => {
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

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this recipe?')) {
      if (id) {
        deleteRecipe(id);
        toast({
          title: "Recipe deleted",
          description: "The recipe has been successfully deleted.",
        });
        navigate('/');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
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
          <Link to="/" className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6">
            <ArrowLeft className="mr-2 h-5 w-5" /> Back to Recipes
          </Link>
          <div className="text-center py-12">
            <h2 className="text-2xl font-medium text-gray-600">Recipe Not Found</h2>
            <p className="text-gray-500 mt-2">The recipe you're looking for doesn't exist.</p>
            <Link 
              to="/" 
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90"
            >
              Go back to all recipes
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const dietaryTags = getDietaryTags(recipe.dietaryRestrictions);
  const avgRating = getAverageRating(recipe.ratings);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/" className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6">
          <ArrowLeft className="mr-2 h-5 w-5" /> Back to Recipes
        </Link>
        
        <article className="bg-white shadow-lg rounded-lg overflow-hidden animate-fade-in">
          <div className="relative h-80 w-full">
            <img 
              src={recipe.image} 
              alt={recipe.name} 
              className="absolute inset-0 h-full w-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            <div className="absolute bottom-0 left-0 p-6 w-full">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">{recipe.name}</h1>
              <p className="text-white/90 text-lg">Cuisine: {recipe.cuisine}</p>
            </div>
          </div>
          
          <div className="p-6">
            <div className="flex flex-wrap items-center justify-between mb-6">
              <div className="flex items-center">
                {dietaryTags.map((tag, index) => (
                  <span key={index} className={`recipe-tag ${tag.class}`}>
                    {tag.text}
                  </span>
                ))}
              </div>
              
              <div className="flex items-center bg-gray-100 rounded-full px-3 py-1 text-sm">
                <Star className="h-5 w-5 text-yellow-500 mr-1" />
                <span>{avgRating} ({recipe.ratings.length} {recipe.ratings.length === 1 ? 'rating' : 'ratings'})</span>
              </div>
            </div>
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Ingredients</h2>
              <ul className="space-y-2 pl-5">
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={index} className="text-gray-700 flex items-start">
                    <span className="inline-block h-2 w-2 rounded-full bg-recipe-primary mt-2 mr-2"></span>
                    {ingredient}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Instructions</h2>
              <ol className="space-y-4 pl-5">
                {recipe.instructions.map((instruction, index) => (
                  <li key={index} className="text-gray-700">
                    <span className="font-medium text-recipe-primary mr-2">{index + 1}.</span> {instruction}
                  </li>
                ))}
              </ol>
            </div>
            
            <div className="flex justify-end mt-8 space-x-3">
              <button
                onClick={handleDelete}
                className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <Trash2 className="mr-2 h-5 w-5" /> Delete Recipe
              </button>
              <Link
                to={`/edit-recipe/${recipe.id}`}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary"
              >
                <Edit className="mr-2 h-5 w-5" /> Edit Recipe
              </Link>
            </div>
          </div>
        </article>
      </main>
    </div>
  );
};

export default RecipeDetailPage;
