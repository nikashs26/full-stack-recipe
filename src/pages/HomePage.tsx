
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
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
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

  // Query for manual recipes
  const { data: manualRecipes = [], isLoading: isManualLoading } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: fetchManualRecipes,
    staleTime: 60000
  });

  // Query for featured recipes with fallback
  const { data: featuredData, isLoading: isFeaturedLoading } = useQuery({
    queryKey: ['featuredRecipes'],
    queryFn: async () => {
      try {
        return await fetchRecipes('pasta', 'Italian');
      } catch (error) {
        console.error('Featured recipes failed, using fallback');
        // Return fallback data
        return {
          results: [
            {
              id: 716429,
              title: "Pasta with Garlic, Scallions, and Broccoli",
              image: "https://img.spoonacular.com/recipes/716429-312x231.jpg",
              imageType: "jpg",
              readyInMinutes: 25,
              summary: "A delicious and healthy pasta dish perfect for any occasion.",
              cuisines: ["Italian"],
              diets: ["vegetarian"],
              isExternal: true
            },
            {
              id: 715538,
              title: "Bruschetta with Tomato and Basil",
              image: "https://img.spoonacular.com/recipes/715538-312x231.jpg",
              imageType: "jpg",
              readyInMinutes: 15,
              summary: "Classic Italian appetizer with fresh tomatoes and basil.",
              cuisines: ["Italian"],
              diets: ["vegetarian"],
              isExternal: true
            }
          ]
        };
      }
    },
    staleTime: 300000
  });

  // Query for quick recipes with fallback
  const { data: quickData, isLoading: isQuickLoading } = useQuery({
    queryKey: ['quickRecipes'],
    queryFn: async () => {
      try {
        return await fetchRecipes('chicken', '');
      } catch (error) {
        console.error('Quick recipes failed, using fallback');
        return {
          results: [
            {
              id: 715415,
              title: "Red Lentil Soup with Chicken and Turnips",
              image: "https://img.spoonacular.com/recipes/715415-312x231.jpg",
              imageType: "jpg",
              readyInMinutes: 25,
              summary: "Quick and nutritious soup perfect for busy weeknights.",
              cuisines: ["Middle Eastern"],
              diets: ["gluten free"],
              isExternal: true
            }
          ]
        };
      }
    },
    staleTime: 300000
  });

  const recipes = Array.isArray(localRecipes) ? localRecipes : [];
  
  // Process featured recipes
  const featuredRecipes = React.useMemo((): SpoonacularRecipe[] => {
    if (!featuredData?.results) return [];
    
    return featuredData.results
      .slice(0, 8)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg',
        isExternal: true
      }));
  }, [featuredData]);

  // Process quick recipes
  const quickRecipes = React.useMemo((): SpoonacularRecipe[] => {
    if (!quickData?.results) return [];
    
    return quickData.results
      .slice(0, 6)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg',
        isExternal: true
      }));
  }, [quickData]);

  // Process popular recipes from manual recipes
  const popularRecipes = React.useMemo(() => {
    if (!Array.isArray(manualRecipes) || manualRecipes.length === 0) return [];
    
    return manualRecipes
      .slice(0, 8)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg'
      }));
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
      .slice(0, 6);
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
      .slice(0, 6);
  }, [recipes]);

  const handleDeleteRecipe = () => {
    // Intentionally empty
  };

  const handleToggleFavorite = (recipe: Recipe) => {
    // Intentionally empty
  };

  const isLoading = isLocalLoading || isFeaturedLoading || isQuickLoading || isManualLoading;

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

          {/* Popular Recipes */}
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
            
            <Carousel className="w-full">
              <CarouselContent className="-ml-4">
                {popularRecipes.length > 0 ? (
                  popularRecipes.map((recipe, i) => (
                    <CarouselItem key={i} className="pl-4 md:basis-1/2 lg:basis-1/3">
                      <ManualRecipeCard recipe={recipe} />
                    </CarouselItem>
                  ))
                ) : (
                  <CarouselItem className="pl-4 basis-full">
                    <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                      <p className="text-gray-500">Loading popular recipes...</p>
                    </div>
                  </CarouselItem>
                )}
              </CarouselContent>
              <CarouselPrevious className="hidden md:flex" />
              <CarouselNext className="hidden md:flex" />
            </Carousel>
          </section>

          {/* Featured Recipes */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <Award className="mr-2 h-6 w-6 text-recipe-secondary" />
                Featured Recipes
              </h2>
              <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                View all →
              </Link>
            </div>
            
            <Carousel className="w-full">
              <CarouselContent className="-ml-4">
                {featuredRecipes.length > 0 ? (
                  featuredRecipes.map((recipe, i) => (
                    <CarouselItem key={i} className="pl-4 md:basis-1/2 lg:basis-1/3">
                      <RecipeCard 
                        recipe={recipe}
                        isExternal={true}
                        onDelete={handleDeleteRecipe}
                      />
                    </CarouselItem>
                  ))
                ) : (
                  <CarouselItem className="pl-4 basis-full">
                    <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                      <p className="text-gray-500">Loading featured recipes...</p>
                    </div>
                  </CarouselItem>
                )}
              </CarouselContent>
              <CarouselPrevious className="hidden md:flex" />
              <CarouselNext className="hidden md:flex" />
            </Carousel>
          </section>

          {/* Quick & Easy */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <Clock className="mr-2 h-6 w-6 text-recipe-secondary" />
                Quick & Easy
              </h2>
              <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                View all →
              </Link>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {quickRecipes.length > 0 ? (
                quickRecipes.slice(0, 3).map((recipe, i) => (
                  <RecipeCard 
                    key={i}
                    recipe={recipe}
                    isExternal={true}
                    onDelete={handleDeleteRecipe}
                  />
                ))
              ) : (
                <div className="col-span-full text-center py-12 border border-dashed border-gray-300 rounded-lg">
                  <p className="text-gray-500">Loading quick recipes...</p>
                </div>
              )}
            </div>
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
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {topRatedRecipes.slice(0, 3).map((recipe, i) => (
                  <RecipeCard 
                    key={i}
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
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {recentRecipes.slice(0, 3).map((recipe, i) => (
                  <RecipeCard 
                    key={i}
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
