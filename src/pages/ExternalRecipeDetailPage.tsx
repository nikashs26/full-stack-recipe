import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, Users, ExternalLink } from 'lucide-react';
import Header from '../components/Header';
import { useToast } from "@/hooks/use-toast";
import { useQuery } from '@tanstack/react-query';
import { fetchRecipeById } from '../lib/spoonacular';
import { SpoonacularRecipe } from '../types/spoonacular';
import { Card, CardContent } from '@/components/ui/card';

const ExternalRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const numericId = id ? parseInt(id) : 0;
  const navigate = useNavigate();
  const { toast } = useToast();
  const [recipe, setRecipe] = useState<SpoonacularRecipe | null>(null);
  
  // Fetch the external recipe data by ID
  const { data, isLoading, error } = useQuery({
    queryKey: ['externalRecipe', numericId],
    queryFn: () => fetchRecipeById(numericId),
    enabled: !!numericId,
    staleTime: 60 * 1000, // 1 minute
    retry: 2,
  });

  useEffect(() => {
    if (data) {
      console.log("Loaded recipe details:", data);
      setRecipe(data);
    }
  }, [data]);

  useEffect(() => {
    if (error) {
      console.error("Error loading recipe:", error);
      toast({
        title: "Error loading recipe",
        description: "Could not load the recipe details. Please try again later.",
        variant: "destructive",
      });
    }
  }, [error, toast]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link to="/" className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6">
            <ArrowLeft className="mr-2 h-5 w-5" /> Back to Recipes
          </Link>
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
            <p className="text-gray-500 mt-2">The recipe you're looking for doesn't exist or couldn't be loaded.</p>
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

  // Extract ingredients from the recipe
  const ingredients = recipe.extendedIngredients || [];
  
  // Extract instructions from the recipe
  let instructions: string[] = [];
  if (recipe.instructions) {
    // Try to extract from HTML instructions
    const cleanInstructions = recipe.instructions.replace(/<[^>]*>/g, '');
    instructions = cleanInstructions.split('. ').filter(i => i.trim().length > 0);
  } else if (recipe.analyzedInstructions && recipe.analyzedInstructions.length > 0) {
    // Or use analyzed instructions
    instructions = recipe.analyzedInstructions[0].steps.map(s => s.step);
  }

  // Extract dietary information
  const dietaryInfo = recipe.diets || [];

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
              alt={recipe.title} 
              className="absolute inset-0 h-full w-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder.svg';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            <div className="absolute bottom-0 left-0 p-6 w-full">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">{recipe.title}</h1>
              <p className="text-white/90 text-lg">
                {recipe.cuisines && recipe.cuisines.length > 0 
                  ? `Cuisine: ${recipe.cuisines.join(', ')}` 
                  : 'Cuisine: Not specified'}
              </p>
            </div>
          </div>
          
          <div className="p-6">
            <div className="flex flex-wrap items-center justify-between mb-6">
              <div className="flex items-center flex-wrap gap-2">
                {dietaryInfo.map((diet, index) => (
                  <span key={index} className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    {diet}
                  </span>
                ))}
                {dietaryInfo.length === 0 && (
                  <span className="text-gray-500 text-sm">No dietary information available</span>
                )}
              </div>
              
              <div className="flex items-center gap-4 mt-3 sm:mt-0">
                {recipe.readyInMinutes && (
                  <div className="flex items-center text-gray-700">
                    <Clock className="h-5 w-5 mr-1" />
                    <span>{recipe.readyInMinutes} min</span>
                  </div>
                )}
                
                {recipe.servings && (
                  <div className="flex items-center text-gray-700">
                    <Users className="h-5 w-5 mr-1" />
                    <span>{recipe.servings} servings</span>
                  </div>
                )}
              </div>
            </div>
            
            {recipe.summary && (
              <Card className="mb-6">
                <CardContent className="pt-6">
                  <h2 className="text-xl font-semibold text-gray-800 mb-3">Summary</h2>
                  <p className="text-gray-700" dangerouslySetInnerHTML={{ __html: recipe.summary }} />
                </CardContent>
              </Card>
            )}
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Ingredients</h2>
              <ul className="space-y-2 pl-5">
                {ingredients.length > 0 ? (
                  ingredients.map((ingredient, index) => (
                    <li key={index} className="text-gray-700 flex items-start">
                      <span className="inline-block h-2 w-2 rounded-full bg-recipe-primary mt-2 mr-2"></span>
                      {ingredient.originalString || `${ingredient.amount} ${ingredient.unit} ${ingredient.name}`}
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500">No ingredients information available</li>
                )}
              </ul>
            </div>
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Instructions</h2>
              {instructions.length > 0 ? (
                <ol className="space-y-4 pl-5">
                  {instructions.map((instruction, index) => (
                    <li key={index} className="text-gray-700">
                      <span className="font-medium text-recipe-primary mr-2">{index + 1}.</span> {instruction}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-gray-500">No instructions available</p>
              )}
            </div>
            
            {recipe.sourceUrl && (
              <div className="flex justify-end mt-8">
                <a
                  href={recipe.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90"
                >
                  <ExternalLink className="mr-2 h-5 w-5" /> View Original Recipe
                </a>
              </div>
            )}
          </div>
        </article>
      </main>
    </div>
  );
};

export default ExternalRecipeDetailPage;
