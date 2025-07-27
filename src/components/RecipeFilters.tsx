import React, { useState, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Plus, X } from 'lucide-react';

type FilterOption = {
  value: string;
  label: string;
  count?: number;
};

const CUISINE_OPTIONS: FilterOption[] = [
  { value: 'American', label: 'American' },
  { value: 'Italian', label: 'Italian' },
  { value: 'Chinese', label: 'Chinese' },
  { value: 'Japanese', label: 'Japanese' },
  { value: 'Mexican', label: 'Mexican' },
  { value: 'Indian', label: 'Indian' },
  { value: 'Thai', label: 'Thai' },
  { value: 'French', label: 'French' },
  { value: 'Mediterranean', label: 'Mediterranean' },
  { value: 'Other', label: 'Other' },
];

const DIET_OPTIONS: FilterOption[] = [
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'gluten-free', label: 'Gluten Free' },
  { value: 'dairy-free', label: 'Dairy Free' },
];

interface RecipeFiltersProps {
  searchQuery: string;
  selectedCuisines: string[];
  selectedDiets: string[];
  onSearchChange: (query: string) => void;
  onCuisineToggle: (cuisine: string) => void;
  onDietToggle: (diet: string) => void;
  onClearFilters: () => void;
}

export const RecipeFilters = ({
  searchQuery,
  selectedCuisines,
  selectedDiets,
  onSearchChange,
  onCuisineToggle,
  onDietToggle,
  onClearFilters,
}: RecipeFiltersProps) => {
  const [customCuisine, setCustomCuisine] = useState('');

  const handleAddCustomCuisine = (e: React.FormEvent) => {
    e.preventDefault();
    if (customCuisine.trim() && !selectedCuisines.includes(customCuisine)) {
      onCuisineToggle(customCuisine.trim());
      setCustomCuisine('');
    }
  };

  const removeCuisine = (cuisine: string) => {
    onCuisineToggle(cuisine);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-medium mb-2">Search Recipes</h3>
        <Input
          placeholder="Search by name or ingredients..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full"
        />
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-sm font-medium">Cuisines</h3>
          {selectedCuisines.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                selectedCuisines.forEach(cuisine => onCuisineToggle(cuisine));
              }}
              className="h-6 px-2 text-xs"
            >
              Clear
            </Button>
          )}
        </div>
        <ScrollArea className="h-40 pr-2">
          <div className="space-y-3">
            {/* Selected Cuisine Badges */}
            {selectedCuisines.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {selectedCuisines.map((cuisine) => (
                  <Badge 
                    key={cuisine} 
                    variant="secondary" 
                    className="flex items-center gap-1"
                  >
                    {cuisine}
                    <button 
                      type="button" 
                      onClick={() => removeCuisine(cuisine)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
            
            {/* Predefined Cuisine Options */}
            <div className="space-y-2">
              {CUISINE_OPTIONS.map((option) => (
                <div key={option.value} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`cuisine-${option.value}`}
                    checked={selectedCuisines.includes(option.value)}
                    onChange={() => onCuisineToggle(option.value)}
                    className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <label
                    htmlFor={`cuisine-${option.value}`}
                    className="ml-2 text-sm text-gray-700"
                  >
                    {option.label}
                  </label>
                </div>
              ))}
            </div>
            
            {/* Custom Cuisine Input */}
            <form onSubmit={handleAddCustomCuisine} className="mt-3 flex gap-2">
              <Input
                type="text"
                value={customCuisine}
                onChange={(e) => setCustomCuisine(e.target.value)}
                placeholder="Add custom cuisine..."
                className="flex-1 text-sm h-9"
              />
              <Button 
                type="submit" 
                size="sm" 
                variant="outline"
                disabled={!customCuisine.trim()}
                className="h-9"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </ScrollArea>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-sm font-medium">Dietary Restrictions</h3>
          {selectedDiets.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                selectedDiets.forEach(diet => onDietToggle(diet));
              }}
              className="h-6 px-2 text-xs"
            >
              Clear
            </Button>
          )}
        </div>
        <div className="space-y-2">
          {DIET_OPTIONS.map((option) => (
            <div key={option.value} className="flex items-center">
              <input
                type="checkbox"
                id={`diet-${option.value}`}
                checked={selectedDiets.includes(option.value)}
                onChange={() => onDietToggle(option.value)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <label
                htmlFor={`diet-${option.value}`}
                className="ml-2 text-sm text-gray-700"
              >
                {option.label}
              </label>
            </div>
          ))}
        </div>
      </div>

      {(selectedCuisines.length > 0 || selectedDiets.length > 0) && (
        <Button
          variant="outline"
          size="sm"
          onClick={onClearFilters}
          className="w-full mt-4"
        >
          Clear All Filters
        </Button>
      )}
    </div>
  );
}
