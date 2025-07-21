import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { loadRecipes } from '../utils/storage';
import { fetchManualRecipes } from '../lib/manualRecipes';
import type { DietaryRestriction } from '../types/recipe';
import { Loader2, Search, Filter, X, Clock, Flame, ChefHat } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import RecipeCard from '@/components/RecipeCard';
import { Input } from '@/components/ui/input';
import { RecipeFilters } from '@/components/RecipeFilters';
import { useDebounce } from '../hooks/useDebounce';
import { useMediaQuery } from '../hooks/use-media-query';
import { Drawer, DrawerContent, DrawerTrigger } from '@/components/ui/drawer';

import Header from '../components/Header';

// Recipe type definitions
type BaseRecipe = {
  id: string | number;
  title: string;
  description?: string;
  image?: string;
  type: 'saved' | 'manual' | 'spoonacular';
  created_at?: string;
  updated_at?: string;
};

type ManualRecipe = BaseRecipe & {
  type: 'manual';
  ready_in_minutes?: number;
  cuisine?: string[];
  diets?: string[];
  ingredients?: Array<{ name: string; amount?: string | number; unit?: string }>;
};

type SpoonacularRecipe = BaseRecipe & {
  type: 'spoonacular';
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  summary?: string;
  analyzedInstructions?: any[];
  cuisines?: string[];
  diets?: string[];
  extendedIngredients?: Array<{
    id: number;
    name: string;
    original: string;
    amount: number;
    unit: string;
  }>;
};

type Recipe = ManualRecipe | SpoonacularRecipe;

type NormalizedRecipe = {
  id: string;
  title: string;
  description: string;
  imageUrl?: string;
  ready_in_minutes?: number;
  servings?: number;
  sourceUrl?: string;
  summary?: string;
  instructions?: string;
  analyzedInstructions?: any[];
  ingredients: Array<{ name: string; amount?: string; unit?: string }>;
  cuisines: string[];
  dietaryRestrictions: string[];
  type: 'saved' | 'manual' | 'spoonacular';
};

// Recommended search items
const recommendedSearches = [
  { icon: <Clock className="w-4 h-4" />, term: 'Quick meals', description: 'Ready in under 30 minutes' },
  { icon: <Flame className="w-4 h-4" />, term: 'Spicy food', description: 'For those who love heat' },
  { icon: <ChefHat className="w-4 h-4" />, term: 'Gourmet', description: 'Restaurant-quality dishes' },
];

const RecipesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showRecommendedSearches, setShowRecommendedSearches] = useState(true);
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [selectedDiets, setSelectedDiets] = useState<string[]>([]);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const isDesktop = useMediaQuery("(min-width: 1024px");
  const debouncedSearchQuery = useDebounce(searchQuery, 500);

  // Define the expected recipe type from the API
  interface ApiRecipe {
    id: string | number;
    title: string;
    description?: string;
    image?: string;
    cuisine?: string[];
    diets?: string[];
    ready_in_minutes?: number;
    type?: 'manual' | 'saved' | 'spoonacular';
  }

  // Fetch all recipes from ChromaDB with search and filters
  const { 
    data: recipes = [], 
    isLoading: isLoadingRecipes, 
    isFetching 
  } = useQuery<ApiRecipe[]>({
    queryKey: ['recipes', debouncedSearchQuery, selectedCuisines, selectedDiets],
    queryFn: async () => {
      // Fetch all recipes by setting a large page size (1000)
      const result = await fetchManualRecipes(debouncedSearchQuery, '', {
        page: 1,
        pageSize: 1000, // Fetch all recipes at once
        cuisines: selectedCuisines,
        diets: selectedDiets
      });
      return result as unknown as ApiRecipe[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchTerm);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Normalize recipes to a common format
  const normalizedRecipes = useMemo<NormalizedRecipe[]>(() => {
    if (!Array.isArray(recipes)) return [];
    
    return recipes.map(recipe => ({
      id: String(recipe.id || Math.random().toString(36).substr(2, 9)),
      title: recipe.title || 'Untitled Recipe',
      description: recipe.description || '',
      imageUrl: recipe.image || '/placeholder-recipe.jpg',
      type: 'manual',
      cuisines: Array.isArray(recipe.cuisine) ? recipe.cuisine : [],
      dietaryRestrictions: Array.isArray(recipe.diets) ? recipe.diets : [],
      ready_in_minutes: recipe.ready_in_minutes || 30,
      ingredients: [],
      servings: 0, // Add default value for servings
      sourceUrl: '', // Add default value for sourceUrl
      summary: '', // Add default value for summary
      analyzedInstructions: [] // Add default value for analyzedInstructions
    }));
  }, [recipes]);

  // All recipes are now loaded at once
  const filteredRecipes = useMemo(() => {
    return normalizedRecipes;
  }, [normalizedRecipes]);

  // Use all filtered recipes (no pagination)
  const displayRecipes = filteredRecipes;

  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    setShowRecommendedSearches(false);
    
    // Scroll to results after a short delay to allow re-render
    const timer = setTimeout(() => {
      const resultsSection = document.getElementById('recipe-results');
      if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const handleRecommendedSearch = (term: string) => {
    handleSearch(term);
    setShowRecommendedSearches(false);
    // Auto-scroll to results
    setTimeout(() => {
      const resultsSection = document.getElementById('recipe-results');
      if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
      }
    }, 300);
  };

  const handleCuisineToggle = (cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine)
        ? prev.filter(c => c !== cuisine)
        : [...prev, cuisine]
    );
  };

  const handleDietToggle = (diet: string) => {
    setSelectedDiets(prev => 
      prev.includes(diet)
        ? prev.filter(d => d !== diet)
        : [...prev, diet]
    );
  };

  const clearAllFilters = () => {
    setSelectedCuisines([]);
    setSelectedDiets([]);
    setSearchQuery("");
  };

  // Show loading state only when we have a search query and data is being fetched
  const isLoading = isLoadingRecipes && searchQuery !== '';
  
  // Add a small delay to prevent flash of loading state for fast responses
  const [showLoading, setShowLoading] = useState(false);
  
  useEffect(() => {
    if (isLoading) {
      const timer = setTimeout(() => setShowLoading(true), 200);
      return () => clearTimeout(timer);
    } else {
      setShowLoading(false);
    }
  }, [isLoading]);

  const renderFilters = () => (
    <div className="lg:w-80 space-y-6 pr-6">
      <RecipeFilters
        searchQuery={searchQuery}
        selectedCuisines={selectedCuisines}
        selectedDiets={selectedDiets}
        onSearchChange={(query: string) => setSearchQuery(query)}
        onCuisineToggle={handleCuisineToggle}
        onDietToggle={handleDietToggle}
        onClearFilters={clearAllFilters}
      />
    </div>
  );

  const renderMobileFilters = () => (
    <Drawer open={showMobileFilters} onOpenChange={setShowMobileFilters}>
      <div className="fixed bottom-6 right-6 z-10 lg:hidden">
        <Button
          onClick={() => setShowMobileFilters(true)}
          className="rounded-full w-14 h-14 shadow-lg"
          size="icon"
        >
          <Filter className="h-6 w-6" />
        </Button>
      </div>
      <DrawerContent className="h-[90vh] px-4 pb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Filters</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowMobileFilters(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        {renderFilters()}
      </DrawerContent>
    </Drawer>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-amber-600 bg-clip-text text-transparent">
            Discover Culinary Delights
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Search through thousands of recipes to find your next favorite meal. Filter by cuisine, dietary needs, or ingredients.
          </p>
        </div>

        {/* Search Bar */}
        <Card className="mx-auto max-w-3xl shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search for recipes..."
                className="pl-10 py-6 text-base border-0 shadow-sm focus-visible:ring-2 focus-visible:ring-primary/50"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onFocus={() => setShowRecommendedSearches(true)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch(searchTerm);
                  }
                }}
              />
              <Button 
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-10"
                onClick={() => handleSearch(searchTerm)}
              >
                Search
              </Button>
            </div>
          </CardHeader>
          
          {/* Recommended Searches */}
          {showRecommendedSearches && !searchTerm && (
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
                {recommendedSearches.map((item, index) => (
                  <Card 
                    key={index} 
                    className="cursor-pointer hover:bg-gray-50 transition-colors border-dashed"
                    onClick={() => handleRecommendedSearch(item.term)}
                  >
                    <CardContent className="p-4 flex items-start space-x-3">
                      <div className="p-2 rounded-full bg-primary/10 text-primary">
                        {item.icon}
                      </div>
                      <div>
                        <h4 className="font-medium">{item.term}</h4>
                        <p className="text-sm text-gray-500">{item.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Filters */}
        <div className="flex flex-col lg:flex-row">
          {/* Desktop Filters */}
          {isDesktop && renderFilters()}
          
          {/* Mobile Filters */}
          {!isDesktop && renderMobileFilters()}
        </div>

        {/* Recipe Results */}
        <div id="recipe-results" className="py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {searchTerm ? `Search Results for "${searchTerm}"` : 'All Recipes'}
              </h2>
              <p className="text-gray-600">
                {filteredRecipes.length} {filteredRecipes.length === 1 ? 'recipe' : 'recipes'} found
              </p>
            </div>

            {showLoading ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                    <div className="bg-gray-300 h-48 rounded-lg mb-4"></div>
                    <div className="bg-gray-300 h-4 rounded mb-2"></div>
                    <div className="bg-gray-300 h-3 rounded w-2/3"></div>
                  </div>
                ))}
              </div>
            ) : filteredRecipes.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {displayRecipes.map((recipe, index) => {
                  // Prepare the recipe object for RecipeCard with proper typing
                  const recipeForCard = {
                    // Required fields
                    id: recipe.id.toString(),
                    title: recipe.title,
                    name: recipe.title, // For backwards compatibility
                    image: recipe.imageUrl || '/placeholder-recipe.jpg',
                    imageUrl: recipe.imageUrl || '/placeholder-recipe.jpg', // For backwards compatibility
                    
                    // Cuisine information
                    cuisines: Array.isArray(recipe.cuisines) ? recipe.cuisines : [],
                    cuisine: Array.isArray(recipe.cuisines) ? recipe.cuisines[0] : '',
                    
                    // Dietary information
                    dietaryRestrictions: (recipe.dietaryRestrictions || []).filter((d: string): d is DietaryRestriction => 
                      ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'].includes(d)
                    ),
                    diets: (recipe.dietaryRestrictions || []).filter((d: string) => 
                      ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'].includes(d)
                    ),
                    
                    // Recipe details
                    ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : [],
                    instructions: Array.isArray(recipe.instructions) 
                      ? recipe.instructions 
                      : recipe.instructions 
                        ? [recipe.instructions] 
                        : ['No instructions available'],
                    description: recipe.description || '',
                    cookingTime: recipe.ready_in_minutes ? `${recipe.ready_in_minutes} minutes` : 'Not specified',
                    servings: recipe.servings || 4,
                    
                    // Source and type information
                    source: recipe.type === 'spoonacular' ? 'spoonacular' : 'local',
                    type: recipe.type || 'saved',
                    
                    // Additional metadata
                    ratings: [],
                    comments: [],
                    difficulty: 'medium',
                    
                    // Add any other fields that might be used by the RecipeCard
                    ...(recipe.type === 'spoonacular' && { source: 'spoonacular' })
                  };
                  
                  return (
                    <div key={`${recipe.type}-${recipe.id}-${index}`} className="h-full">
                      <RecipeCard 
                        recipe={recipeForCard}
                        isExternal={recipe.type === 'spoonacular'}
                        onClick={() => {
                          if (recipe.type === 'spoonacular') {
                            navigate(`/external-recipe/${recipe.id}`, { 
                              state: { source: 'spoonacular' } 
                            });
                          } else {
                            navigate(`/recipe/${recipe.id}`);
                          }
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-100">
                <ChefHat className="mx-auto h-16 w-16 text-gray-300" />
                <h3 className="mt-4 text-xl font-semibold text-gray-700">No recipes found</h3>
                <p className="mt-2 text-gray-500 max-w-md mx-auto">
                  {searchTerm
                    ? 'No recipes match your search. Try adjusting your search term.'
                    : 'No recipes available at the moment. Check back later or add your own recipe!'}
                </p>
                {!searchTerm && (
                  <Button 
                    className="mt-6" 
                    variant="outline"
                    onClick={() => setShowRecommendedSearches(true)}
                  >
                    <Search className="mr-2 h-4 w-4" />
                    Show Recommended Searches
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Showing all results at once */}
        {filteredRecipes.length > 0 && (
          <div className="text-center text-sm text-muted-foreground mt-4">
            Showing all {filteredRecipes.length} recipes
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
