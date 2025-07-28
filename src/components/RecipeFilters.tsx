import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Plus, X, Search, Filter, ChefHat, Leaf } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

type FilterOption = {
  value: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
};

const CUISINE_OPTIONS: FilterOption[] = [
  { value: 'American', label: 'American', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Italian', label: 'Italian', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Chinese', label: 'Chinese', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Japanese', label: 'Japanese', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Mexican', label: 'Mexican', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Indian', label: 'Indian', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Thai', label: 'Thai', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'French', label: 'French', icon: <ChefHat className="w-4 h-4" /> },
  { value: 'Mediterranean', label: 'Mediterranean', icon: <ChefHat className="w-4 h-4" /> },
];

const DIET_OPTIONS: FilterOption[] = [
  { value: 'vegetarian', label: 'Vegetarian', icon: <Leaf className="w-4 h-4" /> },
  { value: 'vegan', label: 'Vegan', icon: <Leaf className="w-4 h-4" /> },
  { value: 'gluten-free', label: 'Gluten Free', icon: <Leaf className="w-4 h-4" /> },
  { value: 'dairy-free', label: 'Dairy Free', icon: <Leaf className="w-4 h-4" /> },
];

interface RecipeFiltersProps {
  searchQuery: string;
  ingredientQuery: string;
  selectedCuisines: string[];
  selectedDiets: string[];
  onSearchChange: (query: string) => void;
  onIngredientChange: (ingredient: string) => void;
  onCuisineToggle: (cuisine: string) => void;
  onDietToggle: (diet: string) => void;
  onClearFilters: () => void;
}

const FilterSection = ({ 
  title, 
  children,
  selectedCount = 0,
  onClear
}: { 
  title: string; 
  children: React.ReactNode;
  selectedCount?: number;
  onClear: () => void;
}) => (
  <Card className="overflow-hidden">
    <CardHeader className="p-4 pb-2">
      <div className="flex items-center justify-between">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Filter className="w-4 h-4" />
          {title}
          {selectedCount > 0 && (
            <span className="ml-1 text-xs bg-primary text-primary-foreground rounded-full px-2 py-0.5">
              {selectedCount}
            </span>
          )}
        </CardTitle>
        {selectedCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
          >
            Clear
          </Button>
        )}
      </div>
    </CardHeader>
    <CardContent className="p-4 pt-0">
      {children}
    </CardContent>
  </Card>
);

const FilterChip = ({ 
  label, 
  selected, 
  onToggle,
  icon 
}: { 
  label: string; 
  selected: boolean; 
  onToggle: () => void;
  icon?: React.ReactNode;
}) => (
  <Button
    variant={selected ? "default" : "outline"}
    size="sm"
    onClick={onToggle}
    className={`h-8 rounded-full px-3 text-sm font-normal gap-2 ${
      selected ? "shadow-sm" : "hover:bg-muted/50"
    }`}
  >
    {icon}
    {label}
    {selected && <X className="ml-1 h-3 w-3" />}
  </Button>
);

export const RecipeFilters = ({
  searchQuery,
  ingredientQuery,
  selectedCuisines,
  selectedDiets,
  onSearchChange,
  onIngredientChange,
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

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {/* Main Recipe Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by recipe name..."
            className="pl-9 h-11 text-base"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
        
        {/* Ingredient Search */}
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
            <span className="text-muted-foreground mr-1">+</span>
            <Search className="h-4 w-4 text-muted-foreground" />
          </div>
          <Input
            placeholder="Search by ingredient (e.g., chicken, pasta, tomatoes)..."
            className="pl-10 h-11 text-base border-primary/20 focus-visible:ring-1 focus-visible:ring-primary/50"
            value={ingredientQuery}
            onChange={(e) => onIngredientChange(e.target.value)}
          />
        </div>
      </div>

      {/* Cuisines Filter */}
      <FilterSection 
        title="Cuisines" 
        selectedCount={selectedCuisines.length}
        onClear={() => selectedCuisines.forEach(c => onCuisineToggle(c))}
      >
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {CUISINE_OPTIONS.map((option) => (
              <FilterChip
                key={option.value}
                label={option.label}
                selected={selectedCuisines.includes(option.value)}
                onToggle={() => onCuisineToggle(option.value)}
                icon={option.icon}
              />
            ))}
          </div>
          
          <form onSubmit={handleAddCustomCuisine} className="flex gap-2">
            <Input
              type="text"
              value={customCuisine}
              onChange={(e) => setCustomCuisine(e.target.value)}
              placeholder="Add custom cuisine..."
              className="flex-1 h-9 text-sm"
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
      </FilterSection>

      {/* Dietary Restrictions Filter */}
      <FilterSection 
        title="Dietary Preferences" 
        selectedCount={selectedDiets.length}
        onClear={() => selectedDiets.forEach(d => onDietToggle(d))}
      >
        <div className="flex flex-wrap gap-2">
          {DIET_OPTIONS.map((option) => (
            <FilterChip
              key={option.value}
              label={option.label}
              selected={selectedDiets.includes(option.value)}
              onToggle={() => onDietToggle(option.value)}
              icon={option.icon}
            />
          ))}
        </div>
      </FilterSection>

      {/* Active Filters */}
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
};
