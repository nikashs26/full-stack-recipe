
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
        const seenIds = new Set();
        const uniqueRecipes = allRecipes
          .filter(recipe => {
            if (!recipe || !recipe.id || seenIds.has(recipe.id)) return false;
            seenIds.add(recipe.id);
            return recipe.title && 
                   !recipe.title.toLowerCase().includes('fallback') &&
                   recipe.image;
          });
        
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

  // Global deduplication system - process all recipes together
  const processedRecipes = React.useMemo(() => {
    console.log('Processing all recipes with global deduplication...');
    
    const globalSeenTitles = new Set<string>();
    const globalSeenIds = new Set<string | number>();
    
    // Helper function to normalize titles for comparison
    const normalizeTitle = (title: string) => {
      return title.toLowerCase().trim().replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, ' ');
    };
    
    // Helper function to check if recipe is already seen
    const isRecipeSeen = (recipe: any, type: string) => {
      const normalizedTitle = normalizeTitle(recipe.title || recipe.name || '');
      const recipeId = `${type}-${recipe.id}`;
      
      if (!normalizedTitle || globalSeenTitles.has(normalizedTitle) || globalSeenIds.has(recipeId)) {
        return true;
      }
      
      globalSeenTitles.add(normalizedTitle);
      globalSeenIds.add(recipeId);
      return false;
    };

    // Process manual recipes for popular section
    const popularRecipes: any[] = [];
    if (Array.isArray(manualRecipes) && manualRecipes.length > 0) {
      for (const recipe of manualRecipes) {
        if (popularRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'manual')) {
          popularRecipes.push({
            ...recipe,
            image: recipe.image || '/placeholder.svg'
          });
        }
      }
    }

    // Process external recipes for featured section
    const featuredRecipes: SpoonacularRecipe[] = [];
    if (featuredData?.results && Array.isArray(featuredData.results)) {
      for (const recipe of featuredData.results) {
        if (featuredRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'external')) {
          featuredRecipes.push({
            ...recipe,
            image: recipe.image || '/placeholder.svg',
            isExternal: true
          });
        }
      }
    }

    // Process local recipes for top rated section
    const topRatedRecipes: Recipe[] = [];
    if (Array.isArray(recipes) && recipes.length > 0) {
      const sortedByRating = [...recipes]
        .filter(recipe => recipe?.ratings?.length)
        .sort((a, b) => {
          const ratingA = getAverageRating(a.ratings || []);
          const ratingB = getAverageRating(b.ratings || []);
          return ratingB - ratingA;
        });

      for (const recipe of sortedByRating) {
        if (topRatedRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'local')) {
          topRatedRecipes.push(recipe);
        }
      }
    }

    // Process local recipes for recent section
    const recentRecipes: Recipe[] = [];
    if (Array.isArray(recipes) && recipes.length > 0) {
      const sortedByDate = [...recipes]
        .sort((a, b) => {
          const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
          const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
          return dateB - dateA;
        });

      for (const recipe of sortedByDate) {
        if (recentRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'local-recent')) {
          recentRecipes.push(recipe);
        }
      }
    }

    console.log('Global deduplication complete:', {
      popular: popularRecipes.length,
      featured: featuredRecipes.length,
      topRated: topRatedRecipes.length,
      recent: recentRecipes.length,
      totalSeen: globalSeenTitles.size
    });

    return {
      popularRecipes,
      featuredRecipes,
      topRatedRecipes,
      recentRecipes
    };
  }, [recipes, manualRecipes, featuredData]);

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
          {/* Personalized Recommendations - Only for authenticated users */}
          {isAuthenticated && <RecommendedRecipes />}

          {/* Popular Manual Recipes - Always show */}
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
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : manualError ? (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-2">Unable to load popular recipes</p>
                <p className="text-sm text-gray-400">Please try refreshing the page</p>
              </div>
            ) : processedRecipes.popularRecipes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {processedRecipes.popularRecipes.map((recipe, i) => (
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
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : processedRecipes.featuredRecipes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {processedRecipes.featuredRecipes.map((recipe, i) => (
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
          {processedRecipes.topRatedRecipes.length > 0 && (
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
                {processedRecipes.topRatedRecipes.map((recipe, i) => (
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
          {processedRecipes.recentRecipes.length > 0 && (
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
                {processedRecipes.recentRecipes.map((recipe, i) => (
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
