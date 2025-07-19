import React, { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchRecipes } from '../lib/spoonacular';
import { loadRecipes } from '../utils/storage';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { filterRecipes } from '../utils/recipeUtils';
import { Recipe } from '../types/recipe';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import ManualRecipeCard from '../components/ManualRecipeCard';
import { SpoonacularRecipe } from '../types/spoonacular';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '../context/AuthContext';
import { ChefHat, Search, Clock, Heart, Star, Clock3, Flame, Leaf } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

// Recommended search items
const recommendedSearches = [
  { icon: <Clock3 className="w-4 h-4" />, term: 'Quick meals', description: 'Ready in under 30 minutes' },
  { icon: <Flame className="w-4 h-4" />, term: 'Spicy food', description: 'For those who love heat' },
  { icon: <Leaf className="w-4 h-4" />, term: 'Vegetarian', description: 'Meat-free options' },
  { icon: <ChefHat className="w-4 h-4" />, term: 'Italian', description: 'Pasta, pizza, and more' },
  { icon: <Heart className="w-4 h-4" />, term: 'Healthy', description: 'Nutritious and delicious' },
  { icon: <Star className="w-4 h-4" />, term: 'Popular', description: 'Top-rated recipes' },
];

const RecipesPage: React.FC = () => {
  // Hooks
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  
  // State management
  const [searchTerm, setSearchTerm] = useState('');
  const [dietaryFilter, setDietaryFilter] = useState('');
  const [cuisineFilter, setCuisineFilter] = useState('');
  const [ingredientTerm, setIngredientTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showRecommendedSearches, setShowRecommendedSearches] = useState(true);
  const recipesPerPage = 12;
  
  // Query for local recipes
  const { data: localRecipes = [], isLoading: localLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
    staleTime: 300000,
  });

  // Query for manual recipes
  const { data: manualRecipes = [], isLoading: manualLoading } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: fetchManualRecipes,
    staleTime: 300000,
  });

  // Query for external recipes
  const { 
    data: externalRecipesResponse, 
    isLoading: externalLoading, 
    error: externalError 
  } = useQuery({
    queryKey: ["externalRecipes", searchTerm, ingredientTerm],
    queryFn: () => fetchRecipes(searchTerm, ingredientTerm),
    enabled: !!searchTerm || !!ingredientTerm,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
  });
  
  // Handle external errors
  useEffect(() => {
    if (externalError) {
      console.error("Error fetching external recipes:", externalError);
      toast({
        title: "Error loading recipes",
        description: "Could not load recipes. Please try again.",
        variant: "destructive",
      });
    }
  }, [externalError, toast]);
  
  // Combine all recipes
  const allRecipes = useMemo(() => {
    const externals = externalRecipesResponse?.results || [];
    return [
      ...(localRecipes || []).map(recipe => ({ ...recipe, type: 'saved' as const })),
      ...(manualRecipes || []).map(recipe => ({ ...recipe, type: 'manual' as const })),
      ...externals.map(recipe => ({ ...recipe, type: 'external' as const }))
    ];
  }, [localRecipes, manualRecipes, externalRecipesResponse]);

  // Get unique cuisines for filter dropdown
  const uniqueCuisines = useMemo(() => {
    const cuisines = new Set<string>();
    allRecipes.forEach(recipe => {
      if (recipe.cuisines) {
        recipe.cuisines.forEach(cuisine => cuisine && cuisines.add(cuisine));
      }
    });
    return Array.from(cuisines).sort();
  }, [allRecipes]);
  
  // Filter recipes based on search and filter criteria
  const filteredRecipes = useMemo(() => {
    const searchTermLower = searchTerm.toLowerCase();
    const ingredientTermLower = ingredientTerm.toLowerCase();
    const cuisineFilterLower = cuisineFilter.toLowerCase();
    const dietaryFilterLower = dietaryFilter.toLowerCase();
    
    return allRecipes.filter(recipe => {
      // Check if recipe matches search term
      const matchesSearch = !searchTerm || 
        (recipe.title || '').toLowerCase().includes(searchTermLower) ||
        (recipe.ingredients?.some(ing => 
          (ing.name || '').toLowerCase().includes(searchTermLower)
        ));
        
      // Check if recipe matches ingredient filter
      const matchesIngredient = !ingredientTerm || 
        (recipe.ingredients?.some(ing => 
          (ing.name || '').toLowerCase().includes(ingredientTermLower)
        ));
        
      // Check if recipe matches dietary filter
      const matchesDietary = !dietaryFilter || 
        (recipe.diets || []).some(diet => 
          diet.toLowerCase() === dietaryFilterLower
        );
        
      // Check if recipe matches cuisine filter
      const matchesCuisine = !cuisineFilter || 
        (recipe.cuisines || []).some(cuisine => 
          cuisine.toLowerCase() === cuisineFilterLower
        );
        
      return matchesSearch && matchesIngredient && matchesDietary && matchesCuisine;
    });
  }, [allRecipes, searchTerm, ingredientTerm, dietaryFilter, cuisineFilter]);
  
  // Get current recipes for pagination
  const totalPages = Math.ceil(filteredRecipes.length / recipesPerPage);
  const startIndex = (currentPage - 1) * recipesPerPage;
  const endIndex = startIndex + recipesPerPage;
  const currentRecipes = useMemo(() => {
    return filteredRecipes.slice(startIndex, endIndex);
  }, [filteredRecipes, startIndex, endIndex]);

  // Loading state
  const isLoading = localLoading || manualLoading || (searchTerm && externalLoading);

  const handleDeleteRecipe = (id: string) => {
    console.log('Delete recipe:', id);
    toast({
      title: "Recipe deletion not implemented",
      description: "This feature will be added soon.",
    });
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handler functions for FilterBar
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const handleIngredientChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientTerm(e.target.value);
    setCurrentPage(1);
  };

  const handleDietaryFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDietaryFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleCuisineFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCuisineFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setIngredientTerm('');
    setDietaryFilter('');
    setCuisineFilter('');
    setCurrentPage(1);
  };

  // Handle search submission
  const handleSearch = (term: string) => {
    setSearchTerm(term);
    setShowRecommendedSearches(false);
    setCurrentPage(1);
  };

  // Handle recommended search click
  const handleRecommendedSearch = (term: string) => {
    handleSearch(term);
    // Auto-scroll to results
    setTimeout(() => {
      const resultsSection = document.getElementById('recipe-results');
      if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
      }
    }, 300);
  };

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

        {/* Enhanced Search Bar */}
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
                onKeyPress={(e) => e.key === 'Enter' && handleSearch(searchTerm)}
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
        <div className="mt-8">
          <FilterBar
            searchTerm={searchTerm}
            ingredientTerm={ingredientTerm}
            dietaryFilter={dietaryFilter}
            cuisineFilter={cuisineFilter}
            cuisines={uniqueCuisines}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            onIngredientChange={(e) => setIngredientTerm(e.target.value)}
            onDietaryFilterChange={(e) => setDietaryFilter(e.target.value)}
            onCuisineFilterChange={(e) => setCuisineFilter(e.target.value)}
            onClearFilters={() => {
              setSearchTerm('');
              setIngredientTerm('');
              setDietaryFilter('');
              setCuisineFilter('');
              setCurrentPage(1);
            }}
          />
        </div>

        {/* All Recipes Section - Only section on this page */}
        <div id="recipe-results" className="mt-12">
          {/* Results Summary */}
          {(searchTerm || ingredientTerm || dietaryFilter || cuisineFilter) && (
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-2">
                {filteredRecipes.length} {filteredRecipes.length === 1 ? 'Recipe' : 'Recipes'} Found
              </h2>
              <div className="flex flex-wrap gap-2">
                {searchTerm && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary/10 text-primary">
                    {searchTerm}
                  </span>
                )}
                {ingredientTerm && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    <span className="mr-1">Ingredient:</span> {ingredientTerm}
                  </span>
                )}
                {dietaryFilter && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    {dietaryFilter}
                  </span>
                )}
                {cuisineFilter && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
                    {cuisineFilter}
                  </span>
                )}
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary"></div>
              <p className="text-gray-600">Finding delicious recipes for you...</p>
            </div>
          ) : (
            <>
              {filteredRecipes.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {currentRecipes.map((recipe, index) => (
                    <div 
                      key={`${recipe.id}-${index}`} 
                      className="h-full transition-transform duration-300 hover:scale-[1.02]"
                    >
                      {recipe.type === 'manual' || recipe.type === 'saved' ? (
                        <ManualRecipeCard recipe={recipe} />
                      ) : (
                        <RecipeCard recipe={{
                          ...recipe,
                          // Ensure all required SpoonacularRecipe fields are present
                          id: recipe.id || 0,
                          title: recipe.title || 'Untitled Recipe',
                          image: recipe.image || '',
                          readyInMinutes: recipe.readyInMinutes || 0,
                          servings: recipe.servings || 0,
                          sourceUrl: recipe.sourceUrl || '',
                          summary: recipe.summary || '',
                          analyzedInstructions: recipe.analyzedInstructions || [],
                          extendedIngredients: recipe.ingredients?.map(ing => ({
                            id: ing.id || 0,
                            name: ing.name || '',
                            original: ing.original || '',
                            amount: ing.amount || 0,
                            unit: ing.unit || '',
                            measures: {
                              metric: {
                                amount: ing.amount || 0,
                                unitShort: ing.unit || '',
                                unitLong: ing.unit || ''
                              },
                              us: {
                                amount: ing.amount || 0,
                                unitShort: ing.unit || '',
                                unitLong: ing.unit || ''
                              }
                            }
                          })) || []
                        }} />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-white/50 rounded-xl border-2 border-dashed border-gray-200">
                  <ChefHat className="mx-auto h-16 w-16 text-gray-300" />
                  <h3 className="mt-4 text-xl font-semibold text-gray-700">No recipes found</h3>
                  <p className="mt-2 text-gray-500 max-w-md mx-auto">
                    {searchTerm || ingredientTerm || dietaryFilter || cuisineFilter
                      ? 'Try adjusting your search or filter criteria. Or try one of our recommended searches.'
                      : 'No recipes available at the moment. Check back later or add your own recipe!'}
                  </p>
                  {!searchTerm && !ingredientTerm && !dietaryFilter && !cuisineFilter && (
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
            </>
          )}
        </div>

        {/* Pagination */}
        {!isLoading && filteredRecipes.length > 0 && (
          <div className="flex justify-center mt-12">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="h-10 w-10 p-0"
              >
                <span className="sr-only">Previous</span>
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </Button>
              {Array.from(
                { length: Math.min(5, Math.ceil(filteredRecipes.length / recipesPerPage)) },
                (_, i) => {
                  // Show first, last, and current page with neighbors
                  const page = i + 1;
                  return (
                    <Button
                      key={page}
                      variant={currentPage === page ? "default" : "outline"}
                      size="sm"
                      className="h-10 w-10 p-0"
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </Button>
                  );
                }
              )}
              {Math.ceil(filteredRecipes.length / recipesPerPage) > 5 && (
                <span className="px-2 text-gray-500">...</span>
              )}
              {Math.ceil(filteredRecipes.length / recipesPerPage) > 5 && (
                <Button
                  variant={
                    currentPage === Math.ceil(filteredRecipes.length / recipesPerPage)
                      ? "default"
                      : "outline"
                  }
                  size="sm"
                  className="h-10 w-10 p-0"
                  onClick={() =>
                    setCurrentPage(Math.ceil(filteredRecipes.length / recipesPerPage))
                  }
                >
                  {Math.ceil(filteredRecipes.length / recipesPerPage)}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setCurrentPage((prev) =>
                    Math.min(prev + 1, Math.ceil(filteredRecipes.length / recipesPerPage))
                  )
                }
                disabled={currentPage >= Math.ceil(filteredRecipes.length / recipesPerPage)}
                className="h-10 w-10 p-0"
              >
                <span className="sr-only">Next</span>
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
