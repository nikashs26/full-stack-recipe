
import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import Header from '../components/Header';
import { loadRecipes } from '../utils/storage';
import { fetchRecipes } from '../lib/spoonacular';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import RecipeCard from '../components/RecipeCard';
import ManualRecipeCard from '../components/ManualRecipeCard';
import { getAverageRating } from '../utils/recipeUtils';
import { ChefHat, TrendingUp, Award, Clock, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '../context/AuthContext';
import RecommendedRecipes from '../components/RecommendedRecipes';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  
  // Query for local recipes
  const { data: localRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
    staleTime: 60000
  });

  // Query for manual recipes with better error handling
  const { data: manualRecipes = [], isLoading: isManualLoading, error: manualError } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: async () => {
      console.log('Fetching manual recipes for homepage...');
      try {
        const recipes = await fetchManualRecipes();
        console.log('Manual recipes fetched:', recipes.length);
        return recipes;
      } catch (error) {
        console.error('Error fetching manual recipes:', error);
        return [];
      }
    },
    staleTime: 60000,
    retry: 2
  });

  // Query for featured external recipes
  const { data: featuredData, isLoading: isFeaturedLoading } = useQuery({
    queryKey: ['featuredRecipes'],
    queryFn: async () => {
      try {
        console.log('Fetching featured recipes...');
        const [pastaResult, chickenResult, vegetarianResult] = await Promise.all([
          fetchRecipes('pasta', 'Italian').catch(() => ({ results: [] })),
          fetchRecipes('chicken', '').catch(() => ({ results: [] })),
          fetchRecipes('vegetarian', '').catch(() => ({ results: [] }))
        ]);
        
        const allRecipes = [
          ...(pastaResult?.results || []),
          ...(chickenResult?.results || []),
          ...(vegetarianResult?.results || [])
        ];
        
        // Remove duplicates and filter out invalid recipes
        const uniqueRecipes = allRecipes
          .filter((recipe, index, self) => 
            recipe && recipe.id && index === self.findIndex(r => r.id === recipe.id)
          )
          .filter(recipe => 
            recipe.title && 
            !recipe.title.toLowerCase().includes('fallback') &&
            recipe.image
          );
        
        console.log('Featured recipes processed:', uniqueRecipes.length);
        return { results: uniqueRecipes.slice(0, 12) };
      } catch (error) {
        console.error('Featured recipes failed:', error);
        return { results: [] };
      }
    },
    staleTime: 300000
  });

  const recipes = Array.isArray(localRecipes) ? localRecipes : [];
  
  // Process featured recipes
  const featuredRecipes = React.useMemo((): SpoonacularRecipe[] => {
    if (!featuredData?.results) return [];
    
    return featuredData.results
      .slice(0, 12)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg',
        isExternal: true
      }));
  }, [featuredData]);

  // Process popular recipes from manual recipes
  const popularRecipes = React.useMemo(() => {
    console.log('Processing popular recipes, manual recipes available:', manualRecipes.length);
    
    if (!Array.isArray(manualRecipes) || manualRecipes.length === 0) {
      console.log('No manual recipes available for popular section');
      return [];
    }
    
    const processed = manualRecipes
      .slice(0, 12)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg'
      }));
      
    console.log('Popular recipes processed:', processed.length);
    return processed;
  }, [manualRecipes]);

  // Top rated local recipes
  const topRatedRecipes = React.useMemo(() => {
    if (!Array.isArray(recipes) || recipes.length === 0) return [];

    return [...recipes]
      .filter(recipe => recipe && recipe.ratings && recipe.ratings.length > 0)
      .sort((a, b) => {
        const ratingA = getAverageRating(a.ratings || []);
        const ratingB = getAverageRating(b.ratings || []);
        return ratingB - ratingA;
      })
      .slice(0, 9);
  }, [recipes]);

  // Recent recipes
  const recentRecipes = React.useMemo(() => {
    if (!Array.isArray(recipes) || recipes.length === 0) return [];

    return [...recipes]
      .sort((a, b) => {
        const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return dateB - dateA;
      })
      .slice(0, 9);
  }, [recipes]);

  const handleDeleteRecipe = () => {
    // Intentionally empty
  };

  const handleToggleFavorite = (recipe: Recipe) => {
    // Intentionally empty
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="pt-24 md:pt-28">
        {/* Hero Section */}
        <section className="relative bg-gradient-to-r from-recipe-accent to-recipe-primary py-16 md:py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Discover Delicious Recipes
              </h1>
              <p className="text-xl text-white/90 mb-8 max-w-3xl mx-auto">
                {isAuthenticated 
                  ? "Your personalized recipe collection awaits" 
                  : "Find, save, and create your favorite recipes all in one place"}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/recipes">
                  <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                    <Search className="mr-2 h-4 w-4" />
                    Browse All Recipes
                  </Button>
                </Link>
                {isAuthenticated ? (
                  <Link to="/preferences">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                      <ChefHat className="mr-2 h-4 w-4" />
                      Update Preferences
                    </Button>
                  </Link>
                ) : (
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Link to="/signin">
                      <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                        Sign In
                      </Button>
                    </Link>
                    <Link to="/signup">
                      <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                        <ChefHat className="mr-2 h-4 w-4" />
                        Sign Up
                      </Button>
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Personalized Recommendations */}
          {isAuthenticated ? (
            <RecommendedRecipes />
          ) : (
            <section className="mb-16">
              <h2 className="text-3xl font-bold text-gray-900 mb-6">Get Personalized Recommendations</h2>
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <p className="text-lg text-gray-700 mb-4">
                  Sign in or create an account to get personalized recipe recommendations based on your preferences!
                </p>
                <div className="flex justify-center gap-4">
                  <Link to="/signin">
                    <Button variant="outline" className="border-recipe-primary text-recipe-primary hover:bg-recipe-primary/10">
                      Sign In
                    </Button>
                  </Link>
                  <Link to="/signup">
                    <Button className="bg-recipe-primary hover:bg-recipe-primary/90">
                      Sign Up Now
                    </Button>
                  </Link>
                </div>
              </div>
            </section>
          )}

          {/* Popular Manual Recipes */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <Award className="mr-2 h-6 w-6 text-recipe-secondary" />
                Popular Recipes
              </h2>
              <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                View all →
              </Link>
            </div>
            
            {isManualLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : manualError ? (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-2">Unable to load popular recipes</p>
                <p className="text-sm text-gray-400">Please try refreshing the page</p>
              </div>
            ) : popularRecipes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {popularRecipes.slice(0, 8).map((recipe, i) => (
                  <ManualRecipeCard key={`popular-${recipe.id}-${i}`} recipe={recipe} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-2">No popular recipes available yet</p>
                <p className="text-sm text-gray-400">Check back soon for new recipes!</p>
              </div>
            )}
          </section>

          {/* Featured External Recipes */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <ChefHat className="mr-2 h-6 w-6 text-recipe-secondary" />
                Featured Recipes
              </h2>
              <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                View all →
              </Link>
            </div>
            
            {isFeaturedLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : featuredRecipes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {featuredRecipes.slice(0, 8).map((recipe, i) => (
                  <RecipeCard 
                    key={`featured-${recipe.id}-${i}`}
                    recipe={recipe}
                    isExternal={true}
                    onDelete={handleDeleteRecipe}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500">Loading featured recipes...</p>
              </div>
            )}
          </section>

          {/* Top Rated Section */}
          {topRatedRecipes.length > 0 && (
            <section className="mb-16">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                  <TrendingUp className="mr-2 h-6 w-6 text-recipe-secondary" />
                  Top Rated Recipes
                </h2>
                <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                  View all →
                </Link>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {topRatedRecipes.slice(0, 8).map((recipe, i) => (
                  <RecipeCard 
                    key={`top-rated-${recipe.id}-${i}`}
                    recipe={recipe}
                    isExternal={false}
                    onDelete={handleDeleteRecipe}
                    onToggleFavorite={handleToggleFavorite}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Recently Added Section */}
          {recentRecipes.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                  <Clock className="mr-2 h-6 w-6 text-recipe-secondary" />
                  Recently Added
                </h2>
                <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                  View all →
                </Link>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {recentRecipes.slice(0, 8).map((recipe, i) => (
                  <RecipeCard 
                    key={`recent-${recipe.id}-${i}`}
                    recipe={recipe}
                    isExternal={false}
                    onDelete={handleDeleteRecipe}
                    onToggleFavorite={handleToggleFavorite}
                  />
                ))}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default HomePage;
