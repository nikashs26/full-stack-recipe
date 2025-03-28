
import React from 'react';
import { Search, PlusCircle, Filter } from 'lucide-react';
import { Link } from 'react-router-dom';

interface FilterBarProps {
  searchTerm: string;
  dietaryFilter: string;
  cuisineFilter: string;
  cuisines: string[];
  onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDietaryFilterChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  onCuisineFilterChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  onClearFilters: () => void;
}

const FilterBar: React.FC<FilterBarProps> = ({
  searchTerm,
  dietaryFilter,
  cuisineFilter,
  cuisines,
  onSearchChange,
  onDietaryFilterChange,
  onCuisineFilterChange,
  onClearFilters
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6 animate-fade-in">
      <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4">
        <div className="relative flex-grow">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input 
            type="text"
            placeholder="Search recipes..." 
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary transition duration-150 ease-in-out sm:text-sm"
            value={searchTerm}
            onChange={onSearchChange}
          />
        </div>
        
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
          <select 
            className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary sm:text-sm"
            value={dietaryFilter}
            onChange={onDietaryFilterChange}
            aria-label="Filter by dietary restriction"
          >
            <option value="">All Diets</option>
            <option value="vegetarian">Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="gluten-free">Gluten-Free</option>
            <option value="carnivore">Carnivore (don't blame us for your bathroom situation)</option>
          </select>
          
          <select 
            className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary sm:text-sm"
            value={cuisineFilter}
            onChange={onCuisineFilterChange}
            aria-label="Filter by cuisine"
          >
            <option value="">All Cuisines</option>
            {cuisines.map(cuisine => (
              <option key={cuisine} value={cuisine}>{cuisine}</option>
            ))}
          </select>
          
          {(searchTerm || dietaryFilter || cuisineFilter) && (
            <button
              onClick={onClearFilters}
              className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary"
            >
              Clear
            </button>
          )}
        </div>
        
        <Link
          to="/add-recipe"
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary transition-colors"
        >
          <PlusCircle className="mr-2 h-5 w-5" /> Add Recipe
        </Link>
      </div>
    </div>
  );
};

export default FilterBar;
