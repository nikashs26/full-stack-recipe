
import React from 'react';
import { Search, PlusCircle, Filter, LayoutGrid } from 'lucide-react';
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
    <div className="bg-white rounded-lg shadow-md p-4 mb-6 animate-fade-in">
      <div className="flex flex-col space-y-3 md:space-y-4">
        {/* Recipe Name Search */}
        <div className="relative flex-grow">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input 
            type="text"
            placeholder="Search recipes by name..." 
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary transition duration-150 ease-in-out sm:text-sm"
            value={searchTerm}
            onChange={onSearchChange}
          />
        </div>
        
        {/* Ingredient Search */}
        <div className="relative flex-grow">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <LayoutGrid className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input 
            type="text"
            placeholder="Search by ingredient (e.g., chicken, tomato)..." 
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary transition duration-150 ease-in-out sm:text-sm"
            value={ingredientTerm}
            onChange={onIngredientChange}
          />
        </div>
        
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
          {/* Dietary Restrictions Filter */}
          <div className="flex-grow">
            <select 
              className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary sm:text-sm"
              value={dietaryFilter}
              onChange={onDietaryFilterChange}
            >
              <option value="">All Dietary Preferences</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
              <option value="gluten-free">Gluten-Free</option>
              <option value="dairy-free">Dairy-Free</option>
              <option value="keto">Keto</option>
              <option value="paleo">Paleo</option>
              <option value="low-carb">Low Carb</option>
              <option value="whole30">Whole30</option>
              <option value="pescetarian">Pescetarian</option>
            </select>
          </div>
          
          {/* Cuisine Filter */}
          <div className="flex-grow">
            <select 
              className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-recipe-primary focus:border-recipe-primary sm:text-sm"
              value={cuisineFilter}
              onChange={onCuisineFilterChange}
            >
              <option value="">All Cuisines</option>
              <option value="american">American</option>
              <option value="italian">Italian</option>
              <option value="mexican">Mexican</option>
              <option value="chinese">Chinese</option>
              <option value="indian">Indian</option>
              <option value="japanese">Japanese</option>
              <option value="thai">Thai</option>
              <option value="french">French</option>
              <option value="mediterranean">Mediterranean</option>
              <option value="korean">Korean</option>
              <option value="spanish">Spanish</option>
              <option value="german">German</option>
              <option value="vietnamese">Vietnamese</option>
              <option value="middle eastern">Middle Eastern</option>
              <option value="british">British</option>
              <option value="caribbean">Caribbean</option>
              <option value="greek">Greek</option>
              <option value="african">African</option>
              <option value="asian">Asian</option>
              <option value="european">European</option>
              {cuisines.map((cuisine) => (
                !['american', 'italian', 'mexican', 'chinese', 'indian', 'japanese', 'thai', 'french', 'mediterranean', 'korean', 'spanish', 'german', 'vietnamese', 'middle eastern', 'british', 'caribbean', 'greek', 'african', 'asian', 'european'].includes(cuisine.toLowerCase()) && (
                  <option key={cuisine} value={cuisine.toLowerCase()}>
                    {cuisine}
                  </option>
                )
              ))}
            </select>
          </div>
          
          {(searchTerm || ingredientTerm || dietaryFilter || cuisineFilter) && (
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
