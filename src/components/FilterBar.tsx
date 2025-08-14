import React from 'react';
import { Search, PlusCircle, Filter, LayoutGrid, X } from 'lucide-react';
import { Link } from 'react-router-dom';

interface FilterBarProps {
  searchTerm: string;
  ingredientTerm: string;
  dietaryFilter: string;
  cuisineFilter: string;
  cuisines: string[];
  onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onIngredientChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDietaryFilterChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  onCuisineFilterChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  onClearFilters: () => void;
}

const FilterBar: React.FC<FilterBarProps> = ({
  searchTerm,
  ingredientTerm,
  dietaryFilter,
  cuisineFilter,
  cuisines,
  onSearchChange,
  onIngredientChange,
  onDietaryFilterChange,
  onCuisineFilterChange,
  onClearFilters
}) => {
  return (
    <div className="rounded-2xl bg-white/80 backdrop-blur p-4 md:p-5 ring-1 ring-gray-200 shadow-sm mb-6 animate-fade-in">
      <div className="flex flex-col gap-3 md:gap-4">
        {/* Recipe Name Search */}
        <div className="relative flex-grow">
          <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" aria-hidden="true" />
          {searchTerm && (
            <button
              type="button"
              onClick={(e) => { e.preventDefault(); onSearchChange({ target: { value: '' } } as any); }}
              aria-label="Clear name search"
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <input
            type="text"
            placeholder="Search recipes by name…"
            className="block w-full h-12 md:h-14 pl-11 pr-10 rounded-full border border-gray-200 bg-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 text-base"
            value={searchTerm}
            onChange={onSearchChange}
            aria-label="Search recipes by name"
          />
        </div>

        {/* Ingredient Search */}
        <div className="relative flex-grow">
          <LayoutGrid className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" aria-hidden="true" />
          {ingredientTerm && (
            <button
              type="button"
              onClick={(e) => { e.preventDefault(); onIngredientChange({ target: { value: '' } } as any); }}
              aria-label="Clear ingredient search"
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <input
            type="text"
            placeholder="Search by ingredient (e.g., chicken, tomato)…"
            className="block w-full h-12 md:h-14 pl-11 pr-10 rounded-full border border-gray-200 bg-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 text-base"
            value={ingredientTerm}
            onChange={onIngredientChange}
            aria-label="Search by ingredient"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <select
            className="block w-full h-12 px-4 border border-gray-200 bg-white rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 text-sm md:text-base"
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
            className="block w-full h-12 px-4 border border-gray-200 bg-white rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 text-sm md:text-base"
            value={cuisineFilter}
            onChange={onCuisineFilterChange}
            aria-label="Filter by cuisine"
          >
            <option value="">All Cuisines</option>
            {cuisines.map(cuisine => (
              <option key={cuisine} value={cuisine}>{cuisine}</option>
            ))}
          </select>

          {(searchTerm || ingredientTerm || dietaryFilter || cuisineFilter) && (
            <button
              onClick={onClearFilters}
              className="inline-flex items-center justify-center px-4 h-12 border border-gray-200 text-sm font-medium rounded-full text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-100"
            >
              Clear
            </button>
          )}
        </div>

        <div className="flex justify-end">
          <Link
            to="/add-recipe"
            className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-full text-white bg-recipe-primary hover:bg-recipe-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary transition-colors"
          >
            <PlusCircle className="mr-2 h-5 w-5" /> Add Recipe
          </Link>
        </div>
      </div>
    </div>
  );
};

export default FilterBar;
