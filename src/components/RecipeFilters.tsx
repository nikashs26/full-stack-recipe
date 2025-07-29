import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, X, Filter, ChefHat, Leaf } from 'lucide-react';
import SearchInput from './SearchInput';
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
    const trimmedCuisine = customCuisine.trim();
    if (trimmedCuisine && !selectedCuisines.includes(trimmedCuisine)) {
      onCuisineToggle(trimmedCuisine);
      setCustomCuisine('');
    }
  };

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

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <SearchInput
        value={searchQuery}
        onChange={onSearchChange}
        placeholder="Search recipes..."
      />

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
          
          <div className="flex gap-2">
            <Input
              type="text"
              value={customCuisine}
              onChange={(e) => setCustomCuisine(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  const trimmedCuisine = customCuisine.trim();
                  if (trimmedCuisine && !selectedCuisines.includes(trimmedCuisine)) {
                    onCuisineToggle(trimmedCuisine);
                    setCustomCuisine('');
                  }
                }
              }}
              placeholder="Add custom cuisine..."
              className="flex-1 h-9 text-sm"
            />
            <Button 
              onClick={(e) => {
                e.preventDefault();
                const trimmedCuisine = customCuisine.trim();
                if (trimmedCuisine && !selectedCuisines.includes(trimmedCuisine)) {
                  onCuisineToggle(trimmedCuisine);
                  setCustomCuisine('');
                }
              }}
              size="sm" 
              variant="outline"
              disabled={!customCuisine.trim()}
              className="h-9"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
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
}
