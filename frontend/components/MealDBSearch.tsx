import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Leaf, X } from 'lucide-react';
import { getApiUrl } from '../config/api';

interface MealDBSearchProps {
  onSearch: (recipes: any[]) => void;
}

const MealDBSearch: React.FC<MealDBSearchProps> = ({ onSearch }) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [cuisine, setCuisine] = useState('');
  const [dietaryPreference, setDietaryPreference] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  interface CuisineOption {
    strArea: string;
  }
  
  const [cuisines, setCuisines] = useState<Array<string | CuisineOption>>([]);

  // Fetch available cuisines on component mount
  useEffect(() => {
    const fetchCuisines = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/recipes/cuisines`);
        if (response.ok) {
          const data = await response.json();
          setCuisines(data);
        }
      } catch (error) {
        console.error('Error fetching cuisines:', error);
      }
    };

    fetchCuisines();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm && !cuisine && !dietaryPreference) return;

    setIsLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (searchTerm) params.append('query', searchTerm);
      if (cuisine) params.append('cuisine', cuisine);
      
      // For dietary preferences, we'll do client-side filtering
      const response = await fetch(`${getApiUrl()}/api/get_recipes?${params.toString()}`);

      if (response.ok) {
        const result = await response.json();
        let recipes = result.results || [];
        
        // Apply dietary filters
        if (dietaryPreference) {
          recipes = recipes.filter((recipe: any) => {
            if (dietaryPreference === 'vegetarian') {
              // Check both the vegetarian flag and ingredients
              const isVegetarian = recipe.vegetarian || 
                !/\b(chicken|beef|pork|fish|shrimp|meat|bacon|sausage|steak|ham|turkey|duck|goose|venison|lamb)\b/i
                  .test((recipe.instructions || '') + ' ' + (recipe.ingredients?.join(' ') || ''));
              return isVegetarian;
            } else if (dietaryPreference === 'vegan') {
              // Check for non-vegan ingredients
              const isVegan = !/\b(meat|chicken|beef|pork|fish|shrimp|bacon|sausage|steak|ham|turkey|duck|goose|venison|lamb|egg|cheese|mozzerella|milk|butter|yogurt|honey|gelatin)\b/i
                .test((recipe.instructions || '') + ' ' + (recipe.ingredients?.join(' ') || ''));
              return isVegan;
            } else if (dietaryPreference === 'gluten-free') {
              // Check for gluten-containing ingredients
              const isGlutenFree = !/\b(wheat|barley|rye|malt|brewer's yeast|triticale|spelt|farina|durum|semolina|graham|einkorn|kamut|bulgur|couscous|seitan|emmer|farro|fu|matzo|matzah|matzoh|mir|udon|wheat|bran|bread|pasta|noodle|flour|breadcrumbs|cracker|breading|batter|coating|stuffing|russet|panko|tempura|wheat germ|wheat berries|wheat bran|wheat starch|wheat grass|wheat grass juice|wheat protein|wheat gluten|wheat germ oil|wheat germ agglutinin|wheat germ extract|wheat grass powder|wheat grass juice powder|wheat grass juice extract|wheat grass juice powder extract|wheat grass juice powder extract concentrate|wheat grass juice powder extract concentrate powder)\b/i
                .test((recipe.instructions || '') + ' ' + (recipe.ingredients?.join(' ') || ''));
              return isGlutenFree;
            }
            return true;
          });
        }
        
        onSearch(recipes);
      }
    } catch (error) {
      console.error('Error searching recipes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecipeClick = (recipe: any) => {
    // Navigate to external recipe detail page with recipe source
    navigate(`/external-recipe/${recipe.id}`, { 
      state: { 
        source: 'themealdb' 
      } 
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <form onSubmit={handleSearch} className="mb-6">
        <div className="bg-white/80 backdrop-blur rounded-2xl ring-1 ring-gray-200 shadow-sm p-3 md:p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            {/* Primary search pill */}
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              {searchTerm && (
                <button
                  type="button"
                  onClick={() => setSearchTerm('')}
                  aria-label="Clear search"
                  className="absolute right-24 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search recipes, e.g. “chicken tikka”"
                aria-label="Search recipes"
                className="w-full h-12 md:h-14 pl-12 pr-28 rounded-full border border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none text-base md:text-lg placeholder:text-gray-400"
              />
              <button
                type="submit"
                disabled={isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-4 md:px-5 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 shadow-sm"
              >
                {isLoading ? 'Searching…' : 'Search'}
              </button>
            </div>

            {/* Cuisine select pill */}
            <div className="relative">
              <Filter className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <select
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                aria-label="Cuisine"
                className="pl-10 pr-8 h-12 rounded-full border border-gray-200 bg-white text-sm md:text-base focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              >
                <option value="">All Cuisines</option>
                {cuisines.map((c, index) => {
                  const cuisineValue = typeof c === 'string' ? c : c.strArea;
                  return (
                    <option key={`${cuisineValue}-${index}`} value={cuisineValue}>
                      {cuisineValue}
                    </option>
                  );
                })}
              </select>
            </div>

            {/* Filters pill */}
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`h-12 px-5 rounded-full border text-sm md:text-base flex items-center gap-2 transition-colors ${showFilters ? 'bg-blue-50 border-blue-500 text-blue-700' : 'bg-white border-gray-200 hover:bg-gray-50'}`}
              aria-expanded={showFilters}
              aria-controls="dietary-filters"
            >
              <Filter className="h-4 w-4" />
              <span>Filters</span>
            </button>
          </div>

          {/* Helper hint */}
          <div className="mt-2 text-xs text-gray-500 px-1">
            Tip: Try queries like “quick pasta”, “vegan burger”, or “Indian curry”.
          </div>
        </div>

        {/* Dietary Filters */}
        {showFilters && (
          <div id="dietary-filters" className="mt-4 p-4 bg-gray-50 rounded-xl ring-1 ring-gray-100">
            <h3 className="font-medium text-gray-700 mb-3">Dietary preferences</h3>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setDietaryPreference(dietaryPreference === 'vegetarian' ? '' : 'vegetarian')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-colors ${dietaryPreference === 'vegetarian' ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-white border border-gray-300 hover:bg-gray-50'}`}
              >
                <Leaf className="h-4 w-4" />
                <span>Vegetarian</span>
              </button>
              <button
                type="button"
                onClick={() => setDietaryPreference(dietaryPreference === 'vegan' ? '' : 'vegan')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-colors ${dietaryPreference === 'vegan' ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-white border border-gray-300 hover:bg-gray-50'}`}
              >
                <Leaf className="h-4 w-4" />
                <span>Vegan</span>
              </button>
              <button
                type="button"
                onClick={() => setDietaryPreference(dietaryPreference === 'gluten-free' ? '' : 'gluten-free')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-colors ${dietaryPreference === 'gluten-free' ? 'bg-blue-100 text-blue-800 border border-blue-300' : 'bg-white border border-gray-300 hover:bg-gray-50'}`}
              >
                <span>Gluten Free</span>
              </button>
            </div>
            {dietaryPreference && (
              <div className="mt-3 text-sm text-gray-600">
                <span className="font-medium">Active filter:</span> {dietaryPreference}
                <button
                  onClick={() => setDietaryPreference('')}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        )}
      </form>
    </div>
  );
};

export default MealDBSearch;
