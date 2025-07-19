
import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import ManualRecipeCard from '../components/ManualRecipeCard';
import { loadRecipes } from '../utils/storage';
import { fetchRecipes } from '../lib/spoonacular';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { filterRecipes } from '../utils/recipeUtils';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '../context/AuthContext';
import { ChefHat } from 'lucide-react';

const RecipesPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [dietaryFilter, setDietaryFilter] = useState('');
  const [cuisineFilter, setCuisineFilter] = useState('');
  const [ingredientTerm, setIngredientTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const recipesPerPage = 12;

  // Load local recipes
  const loadLocalRecipes = async (): Promise<Recipe[]> => {
    try {
      console.log('Loading local recipes from storage...');
      const recipes = await loadRecipes();
      console.log(`Loaded ${recipes.length} recipes from MongoDB`);
      return Array.isArray(recipes) ? recipes : [];
    } catch (error) {
      console.error('Error fetching recipes from MongoDB:', error);
      return [];
    }
  };

  const { data: localRecipes = [], isLoading: localLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadLocalRecipes,
    staleTime: 300000,
  });

  // Query for manual recipes
  const { data: manualRecipes = [], isLoading: manualLoading } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: fetchManualRecipes,
    staleTime: 300000,
  });

  // Query for external recipes - load by default and filter based on search
  const { data: externalData = { results: [] }, isLoading: externalLoading } = useQuery({
    queryKey: ['externalRecipes', searchTerm, ingredientTerm],
    queryFn: async () => {
      console.log(`Fetching recipes with query: "${searchTerm}" and ingredient: "${ingredientTerm}"`);
      
      try {
        const response = await fetchRecipes(searchTerm, ingredientTerm);
        console.log('API Response:', response);
        
        if (response && Array.isArray(response.results)) {
          const validRecipes = response.results.filter(recipe => 
            recipe && 
            recipe.id && 
            recipe.title
          );
          
          console.log(`Fetched ${validRecipes.length} valid external recipes`);
          return { results: validRecipes };
        }
        
        return { results: [] };
      } catch (error) {
        console.error('Error fetching external recipes:', error);
        return { results: [] };
      }
    },
    staleTime: 300000,
  });
  
  const externalRecipes = externalData.results || [];

  const filteredLocalRecipes = useMemo(() => {
    return filterRecipes(localRecipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);
  }, [localRecipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);

  const filteredManualRecipes = useMemo(() => {
    if (!Array.isArray(manualRecipes)) return [];
    
    return manualRecipes.filter(recipe => {
      if (!recipe) return false;
      
      const recipeTitle = recipe.title || "";
      const searchTermLower = searchTerm ? searchTerm.toLowerCase() : "";
      const matchesSearchTerm = searchTerm ? recipeTitle.toLowerCase().includes(searchTermLower) : true;
      
      const recipeCuisines = recipe.cuisine || [];
      const cuisineFilterLower = cuisineFilter ? cuisineFilter.toLowerCase() : "";
      const matchesCuisine = cuisineFilter 
        ? recipeCuisines.some(c => c && c.toLowerCase().includes(cuisineFilterLower))
        : true;
      
      const recipeDiets = recipe.diets || [];
      const matchesDietary = dietaryFilter 
        ? recipeDiets.some(d => d && d.toLowerCase().includes(dietaryFilter.toLowerCase()))
        : true;

      return matchesSearchTerm && matchesCuisine && matchesDietary;
    });
  }, [manualRecipes, searchTerm, cuisineFilter, dietaryFilter]);

  const allRecipes = [
    ...filteredLocalRecipes.map(recipe => ({ ...recipe, type: 'local' })),
    ...filteredManualRecipes.map(recipe => ({ ...recipe, type: 'manual' })),
    ...externalRecipes.map(recipe => ({ ...recipe, type: 'external' }))
  ];

  const totalRecipes = allRecipes.length;
  const totalPages = Math.ceil(totalRecipes / recipesPerPage);
  const startIndex = (currentPage - 1) * recipesPerPage;
  const endIndex = startIndex + recipesPerPage;
  const currentRecipes = allRecipes.slice(startIndex, endIndex);

  const isLoading = localLoading || manualLoading || externalLoading;

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

  // Get unique cuisines from local recipes for the filter
  const uniqueCuisines = useMemo(() => {
    const cuisines = new Set<string>();
    localRecipes.forEach(recipe => {
      if (recipe.cuisine) {
        cuisines.add(recipe.cuisine);
      }
    });
    return Array.from(cuisines).sort();
  }, [localRecipes]);

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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="pt-24 md:pt-28">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-8 text-center">
            Recipe Collection
          </h1>
          
          <FilterBar
            searchTerm={searchTerm}
            onSearchChange={handleSearchChange}
            dietaryFilter={dietaryFilter}
            onDietaryFilterChange={handleDietaryFilterChange}
            cuisineFilter={cuisineFilter}
            onCuisineFilterChange={handleCuisineFilterChange}
            ingredientTerm={ingredientTerm}
            onIngredientChange={handleIngredientChange}
            cuisines={uniqueCuisines}
            onClearFilters={handleClearFilters}
          />

          {/* All Recipes Section - Only section on this page */}
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <ChefHat className="mr-2 h-6 w-6 text-recipe-secondary" />
                All Recipes
              </h2>
              <span className="text-sm text-gray-500">
                {totalRecipes} recipe{totalRecipes !== 1 ? 's' : ''} found
              </span>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : currentRecipes.length > 0 ? (
              <>
                {/* Debug info */}
                <div className="mb-4 p-4 bg-blue-100 rounded-lg">
                  <h3 className="font-bold">Debug Info:</h3>
                  <p>Local recipes: {localRecipes.length}</p>
                  <p>Manual recipes: {manualRecipes.length}</p>
                  <p>External recipes: {externalRecipes.length}</p>
                  <p>All recipes: {allRecipes.length}</p>
                  <p>Current recipes: {currentRecipes.length}</p>
                  <p>Loading states: local={localLoading.toString()}, manual={manualLoading.toString()}, external={externalLoading.toString()}</p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {currentRecipes.map((recipe, index) => {
                    const key = `${recipe.type}-${recipe.id}-${index}`;
                    
                    if (recipe.type === 'manual') {
                      return (
                        <ManualRecipeCard 
                          key={key}
                          recipe={recipe}
                        />
                      );
                    }
                    
                    return (
                      <RecipeCard 
                        key={key}
                        recipe={recipe}
                        isExternal={recipe.type === 'external'}
                        onDelete={handleDeleteRecipe}
                      />
                    );
                  })}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-center items-center space-x-2 mt-8">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
                    >
                      Previous
                    </button>
                    
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(pageNum => (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`px-3 py-2 rounded-md ${
                          currentPage === pageNum
                            ? 'bg-recipe-primary text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {pageNum}
                      </button>
                    ))}
                    
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-4">No recipes found matching your criteria.</p>
                <p className="text-sm text-gray-400">Try adjusting your search filters or search terms.</p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
};

export default RecipesPage;
