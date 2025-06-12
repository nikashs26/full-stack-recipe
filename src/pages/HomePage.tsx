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

// Define a type that combines Recipe and SpoonacularRecipe with isExternal flag
type CombinedRecipe = (Recipe & { isExternal?: boolean }) | (SpoonacularRecipe & { isExternal: boolean });

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  
  // Query for local recipes
  const { data: localRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
    staleTime: 60000
  });

  // Query for manual recipes (popular recipes) - ONLY fetch on homepage
  const { data: manualRecipes = [], isLoading: isManualLoading } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: fetchManualRecipes,
    staleTime: 60000
  });

  // Query for featured recipes (using a popular search term)
  const { data: featuredData, isLoading: isFeaturedLoading } = useQuery({
    queryKey: ['featuredRecipes'],
    queryFn: () => fetchRecipes('pasta', 'Italian'),
    staleTime: 300000
  });

  // Query for quick recipes (less than 30 mins)
  const { data: quickData, isLoading: isQuickLoading } = useQuery({
    queryKey: ['quickRecipes'],
    queryFn: () => fetchRecipes('chicken', ''),
    staleTime: 300000
  });

  // Handle null check for recipes
  const recipes = Array.isArray(localRecipes) ? localRecipes : [];
  
  // Process and get top rated recipes from local collection - KEEP as local recipes with proper linking
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

  // Process featured recipes - ensure they're properly formatted
  const featuredRecipes = React.useMemo((): SpoonacularRecipe[] => {
    if (!featuredData?.results) {
      // Provide fallback featured recipes with correct SpoonacularRecipe structure
      return [
        {
          id: 716429,
          title: "Pasta with Garlic, Scallions, and Broccoli",
          image: "https://img.spoonacular.com/recipes/716429-312x231.jpg",
          imageType: "jpg",
          readyInMinutes: 25,
          summary: "A delicious and healthy pasta dish perfect for any occasion.",
          cuisines: ["Italian"],
          diets: ["vegetarian"]
        },
        {
          id: 715538,
          title: "Bruschetta with Tomato and Basil",
          image: "https://img.spoonacular.com/recipes/715538-312x231.jpg",
          imageType: "jpg",
          readyInMinutes: 15,
          summary: "Classic Italian appetizer with fresh tomatoes and basil.",
          cuisines: ["Italian"],
          diets: ["vegetarian"]
        },
        {
          id: 782585,
          title: "Cannellini Bean and Sausage Soup",
          image: "https://img.spoonacular.com/recipes/782585-312x231.jpg",
          imageType: "jpg",
          readyInMinutes: 30,
          summary: "Hearty Italian soup with beans and sausage.",
          cuisines: ["Italian"],
          diets: []
        }
      ] as SpoonacularRecipe[];
    }
    
    return featuredData.results
      .slice(0, 8)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg'
      }));
  }, [featuredData]);

  // Process quick recipes - ensure they have data
  const quickRecipes = React.useMemo((): SpoonacularRecipe[] => {
    if (!quickData?.results) {
      // Provide fallback quick recipes with correct SpoonacularRecipe structure
      return [
        {
          id: 715415,
          title: "Red Lentil Soup with Chicken and Turnips",
          image: "https://img.spoonacular.com/recipes/715415-312x231.jpg",
          imageType: "jpg",
          readyInMinutes: 25,
          summary: "Quick and nutritious soup perfect for busy weeknights.",
          cuisines: ["Middle Eastern"],
          diets: ["gluten free"]
        },
        {
          id: 716406,
          title: "Asparagus and Pea Soup",
          image: "https://img.spoonacular.com/recipes/716406-312x231.jpg",
          imageType: "jpg",
          readyInMinutes: 20,
          summary: "Light and fresh spring soup.",
          cuisines: ["European"],
          diets: ["vegetarian", "vegan"]
        },
        {
          id: 644387,
          title: "Garlicky Kale",
          image: "https://img.spoonacular.com/recipes/644387-312x231.jpg",
          imageType: "jpg",
          readyInMinutes: 15,
          summary: "Quick and healthy sautéed kale with garlic.",
          cuisines: ["American"],
          diets: ["vegetarian", "vegan"]
        }
      ] as SpoonacularRecipe[];
    }
    
    return quickData.results
      .filter(recipe => recipe && recipe.readyInMinutes && recipe.readyInMinutes <= 30)
      .slice(0, 6)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg'
      }));
  }, [quickData]);

  // Recent recipes (latest added locally) - KEEP as local recipes with proper linking
  const recentRecipes = React.useMemo(() => {
    if (!Array.isArray(recipes) || recipes.length === 0) return [];

    return [...recipes]
      .sort((a, b) => {
        // Sort by most recently added
        const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return dateB - dateA;
      })
      .slice(0, 6);
  }, [recipes]);

  // Process manual recipes for popular section - format properly as ManualRecipe for correct linking
  const popularRecipes = React.useMemo(() => {
    if (!Array.isArray(manualRecipes) || manualRecipes.length === 0) return [];
    
    return manualRecipes
      .slice(0, 8)
      .map(recipe => ({
        ...recipe,
        image: recipe.image || '/placeholder.svg'
      }));
  }, [manualRecipes]);

  // Skip recipe delete functionality on homepage
  const handleDeleteRecipe = () => {
    // This is intentionally empty as we don't want delete functionality on the homepage cards
  };

  // Handle recipe toggle favorite functionality
  const handleToggleFavorite = (recipe: Recipe) => {
    // This is intentionally empty as we don't want favorite functionality on the homepage cards
  };

  // Clean featured recipes to avoid duplicates
  const isLoading = isLocalLoading || isFeaturedLoading || isQuickLoading || isManualLoading;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Add margin-top to account for the fixed header */}
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
          {/* Personalized Recommendations Section */}
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

          {/* Popular Recipes Section - ONLY ON HOMEPAGE */}
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
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <CarouselItem key={i} className="pl-4 md:basis-1/2 lg:basis-1/3">
                      <div className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                    </CarouselItem>
                  ))
                ) : popularRecipes.length > 0 ? (
                  popularRecipes.map((recipe, i) => (
                    <CarouselItem key={i} className="pl-4 md:basis-1/2 lg:basis-1/3">
                      <ManualRecipeCard 
                        recipe={recipe}
                      />
                    </CarouselItem>
                  ))
                ) : (
                  <CarouselItem className="pl-4 basis-full">
                    <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                      <p className="text-gray-500">No popular recipes available</p>
                    </div>
                  </CarouselItem>
                )}
              </CarouselContent>
              <CarouselPrevious className="hidden md:flex" />
              <CarouselNext className="hidden md:flex" />
            </Carousel>
          </section>

          {/* Featured Recipes Section */}
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
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <CarouselItem key={i} className="pl-4 md:basis-1/2 lg:basis-1/3">
                      <div className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                    </CarouselItem>
                  ))
                ) : featuredRecipes.length > 0 ? (
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
                      <p className="text-gray-500">No featured recipes available</p>
                    </div>
                  </CarouselItem>
                )}
              </CarouselContent>
              <CarouselPrevious className="hidden md:flex" />
              <CarouselNext className="hidden md:flex" />
            </Carousel>
          </section>

          {/* Quick & Easy Section */}
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
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))
              ) : quickRecipes.length > 0 ? (
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
                  <p className="text-gray-500">No quick recipes available</p>
                </div>
              )}
            </div>
          </section>

          {/* Top Rated Section (from local recipes) - Keep as local recipes */}
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

          {/* Recently Added Section - Keep as local recipes */}
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
