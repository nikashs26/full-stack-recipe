import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Clock, Utensils, Filter, Leaf, Egg } from 'lucide-react';
import RecipeCard from './RecipeCard';

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
        const response = await fetch('http://localhost:5003/api/recipes/cuisines');
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
      const response = await fetch(
        `http://localhost:5003/get_recipes?${params.toString()}`
      );

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
              const isVegan = !/\b(meat|chicken|beef|pork|fish|shrimp|bacon|sausage|steak|ham|turkey|duck|goose|venison|lamb|egg|cheese|milk|butter|yogurt|honey|gelatin)\b/i
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
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search for recipes..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div className="flex gap-2">
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <select
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
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

            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${showFilters ? 'bg-blue-50 border-blue-500' : 'border-gray-300'}`}
            >
              <Filter className="h-4 w-4" />
              <span>Filters</span>
            </button>
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center justify-center"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Dietary Filters */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-700 mb-3">Dietary Preferences</h3>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setDietaryPreference(dietaryPreference === 'vegetarian' ? '' : 'vegetarian')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm ${dietaryPreference === 'vegetarian' ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-white border border-gray-300'}`}
              >
                <Leaf className="h-4 w-4" />
                <span>Vegetarian</span>
              </button>
              <button
                type="button"
                onClick={() => setDietaryPreference(dietaryPreference === 'vegan' ? '' : 'vegan')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm ${dietaryPreference === 'vegan' ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-white border border-gray-300'}`}
              >
                <Leaf className="h-4 w-4" />
                <span>Vegan</span>
              </button>
              <button
                type="button"
                onClick={() => setDietaryPreference(dietaryPreference === 'gluten-free' ? '' : 'gluten-free')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm ${dietaryPreference === 'gluten-free' ? 'bg-blue-100 text-blue-800 border border-blue-300' : 'bg-white border border-gray-300'}`}
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
