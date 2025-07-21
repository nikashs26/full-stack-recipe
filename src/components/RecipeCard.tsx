
import React from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, Star, Clock, Heart } from 'lucide-react';
import { Recipe } from '../types/recipe';

// Extended recipe type to handle various sources
type ExtendedRecipe = Recipe & {
  title?: string;
  imageUrl?: string;
  cuisines?: string | string[];
  cuisine?: string;
  diets?: string[];
  source?: string;
  ready_in_minutes?: number;
  rating?: number | Array<{ score: number; count: number }>;
  ratings?: number | Array<{ score: number; count: number }>;
};

interface RecipeCardProps {
  recipe: ExtendedRecipe;
  isExternal?: boolean;
  onDelete?: (id: string) => void;
  onClick?: (recipe: ExtendedRecipe) => void;
}

const RecipeCard: React.FC<RecipeCardProps> = React.memo(({ 
  recipe, 
  isExternal = false, 
  onDelete,
  onClick 
}) => {
  // Handle recipe name from various sources
  const recipeName = React.useMemo(() => 
    recipe.name || recipe.title || "Untitled Recipe", 
    [recipe.name, recipe.title]
  );
  
  // Handle cuisine from various formats
  const cuisines = React.useMemo(() => {
    if (Array.isArray(recipe.cuisines)) return recipe.cuisines;
    if (typeof recipe.cuisines === 'string') return [recipe.cuisines];
    if (recipe.cuisine) return [recipe.cuisine];
    return [];
  }, [recipe.cuisines, recipe.cuisine]);
  
  // Handle dietary restrictions from various formats with normalization
  const dietaryRestrictions = React.useMemo(() => {
    // Get from either dietaryRestrictions or diets field
    const restrictions: string[] = [];
    
    const addRestrictions = (items: unknown) => {
      if (!Array.isArray(items)) return;
      
      for (const item of items) {
        try {
          if (item !== null && item !== undefined) {
            restrictions.push(String(item));
          }
        } catch (e) {
          // Skip invalid items
        }
      }
    };
    
    addRestrictions(recipe.dietaryRestrictions);
    addRestrictions(recipe.diets);
    
    // Normalize the values
    return restrictions
      .map(str => {
        const normalized = str.trim().toLowerCase();
        
        // Map common variations to standard values
        switch(normalized) {
          case 'vegetarian':
          case 'veg':
            return 'vegetarian';
          case 'vegan':
          case 'vegan friendly':
            return 'vegan';
          case 'gluten free':
          case 'gluten-free':
          case 'gf':
            return 'gluten-free';
          case 'dairy free':
          case 'dairy-free':
          case 'lactose free':
            return 'dairy-free';
          default:
            return normalized;
        }
      })
      .filter(Boolean) // Remove any empty strings
      .filter((value, index, self) => self.indexOf(value) === index); // Remove duplicates
  }, [recipe.dietaryRestrictions, recipe.diets]);
  
  // Handle image from various sources
  const imageUrl = React.useMemo((): string => {
    if (recipe.image) return recipe.image;
    if (recipe.imageUrl) return recipe.imageUrl;
    if (recipe.source === 'TheMealDB' && recipe.id) {
      const ingredientName = typeof recipe.id === 'string' ? recipe.id.split('_').pop() : '';
      return `https://www.themealdb.com/images/ingredients/${ingredientName || 'placeholder'}.jpg`;
    }
    return '/placeholder.svg';
  }, [recipe.image, recipe.imageUrl, recipe.source, recipe.id]);
  
  // Handle ID from various sources
  const recipeId = React.useMemo((): string => {
    if (recipe.id === null || recipe.id === undefined) return '';
    return String(recipe.id).replace('mealdb_', '');
  }, [recipe.id]);
  
  // Calculate average rating if ratings is an array
  const averageRating = React.useMemo(() => {
    const getAverage = (value: unknown): number | undefined => {
      if (typeof value === 'number') {
        return value;
      }
      
      if (Array.isArray(value)) {
        const validRatings = value
          .filter((r): r is { score: number } => 
            r !== null && 
            typeof r === 'object' && 
            'score' in r && 
            typeof (r as { score: unknown }).score === 'number'
          )
          .map(r => r.score);
          
        if (validRatings.length === 0) return undefined;
        const sum = validRatings.reduce((acc, score) => acc + score, 0);
        return sum / validRatings.length;
      }
      
      return undefined;
    };
    
    return getAverage(recipe.rating) ?? getAverage(recipe.ratings);
  }, [recipe.rating, recipe.ratings]);
  
  // Handle ingredients from various formats
  const ingredients = React.useMemo(() => {
    if (!recipe.ingredients) return [];
    
    return recipe.ingredients.map(ing => {
      if (typeof ing === 'string') {
        return { name: ing, amount: '', unit: '' };
      }
      
      // Handle case where ing is an object
      const name = (ing as any)?.name || '';
      const amount = (ing as any)?.amount;
      const unit = (ing as any)?.unit || '';
      
      return {
        name,
        amount: amount !== undefined ? String(amount) : '',
        unit
      };
    });
  }, [recipe.ingredients]);
  
  // Handle source-specific navigation
  const getRecipePath = React.useCallback((): string => {
    const id = recipe.id !== null && recipe.id !== undefined ? String(recipe.id) : '';
    if (isExternal) {
      return `/external-recipes/${encodeURIComponent(id)}`;
    }
    return `/recipes/${id}`;
  }, [recipe.id, isExternal]);
  
  // Handle card click
  const handleClick = React.useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    if (onClick) {
      onClick(recipe);
    } else {
      const path = getRecipePath();
      if (path) {
        window.location.href = path;
      }
    }
  }, [onClick, recipe, getRecipePath]);

  return (
    <div 
      className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer"
      onClick={handleClick}
    >
      <Link to={getRecipePath()} onClick={(e) => e.stopPropagation()}>
        <div className="relative h-48 overflow-hidden">
          <img
            src={imageUrl}
            alt={recipeName}
            className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              if (target.src !== "/placeholder.svg") {
                target.src = "/placeholder.svg";
              }
            }}
          />
        </div>
        
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {recipeName}
          </h3>
          
          {/* Cuisine Tags */}
          {cuisines.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              {cuisines.map((cuisine, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                >
                  {cuisine}
                </span>
              ))}
            </div>
          )}
          
          {/* Dietary restrictions with icons */}
          {dietaryRestrictions.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {dietaryRestrictions.map((diet) => {
                // Define icons and colors for different diet types
                const getDietInfo = (d: string) => {
                  switch(d) {
                    case 'vegetarian':
                      return { icon: '🥕', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' };
                    case 'vegan':
                      return { icon: '🌱', color: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200' };
                    case 'gluten-free':
                      return { icon: '🌾', color: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200' };
                    case 'dairy-free':
                      return { icon: '🥛', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' };
                    default:
                      return { icon: '🍽️', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' };
                  }
                };
                
                const { icon, color } = getDietInfo(diet);
                
                return (
                  <span 
                    key={diet} 
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}
                    title={diet.charAt(0).toUpperCase() + diet.slice(1)}
                  >
                    <span className="mr-1">{icon}</span>
                    {diet.split('-').map(word => 
                      word.charAt(0).toUpperCase() + word.slice(1)
                    ).join('-')}
                  </span>
                );
              })}
            </div>
          )}
          
          {/* Ingredients Preview */}
          {ingredients.length > 0 && (
            <div className="mt-2">
              <p className="text-sm text-gray-500 line-clamp-2">
                {ingredients.slice(0, 3).map(ing => ing.name).join(', ')}
                {ingredients.length > 3 ? '...' : ''}
              </p>
            </div>
          )}
          
          {/* Recipe Metadata */}
          <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              <span>{recipe.ready_in_minutes ? `${recipe.ready_in_minutes} min` : 'N/A'}</span>
            </div>
            <div className="flex items-center">
              <Star className="w-4 h-4 text-yellow-400 mr-1" />
              <span>{averageRating !== undefined ? Number(averageRating).toFixed(1) : 'N/A'}</span>
            </div>
          </div>
        </div>
      </Link>
      
      {/* Admin actions */}
      {onDelete && (
        <div className="p-4 bg-gray-50 border-t border-gray-100 flex justify-end">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(recipe.id as string);
            }}
            className="text-red-600 hover:text-red-800 text-sm font-medium flex items-center"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Delete Recipe
          </button>
        </div>
      )}
    </div>
  );
});

export default RecipeCard;
