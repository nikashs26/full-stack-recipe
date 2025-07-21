import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Clock, Utensils, Filter } from 'lucide-react';
import RecipeCard from './RecipeCard';

interface MealDBSearchProps {
  onSearch: (recipes: any[]) => void;
}

const MealDBSearch: React.FC<MealDBSearchProps> = ({ onSearch }) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [cuisine, setCuisine] = useState('');
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
    if (!searchTerm && !cuisine) return;

    setIsLoading(true);
    try {
          // Call TheMealDB API endpoint
      const response = await fetch(
        `http://localhost:5003/api/mealdb/search?query=${encodeURIComponent(
          searchTerm
        )}${cuisine ? `&cuisine=${encodeURIComponent(cuisine)}` : ''}`
      );

      if (response.ok) {
        const data = await response.json();
        onSearch(data);
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
            type="submit"
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center justify-center"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default MealDBSearch;
