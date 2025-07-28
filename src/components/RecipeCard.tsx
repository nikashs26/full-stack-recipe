
import React from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, Star, Clock, Heart, Utensils, Clock3, Users, BarChart2 } from 'lucide-react';
import { Recipe } from '../types/recipe';
import { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card';

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
  
  // Debug log the recipe data
  React.useEffect(() => {
    console.log('Recipe data:', {
      id: recipe.id,
      name: recipeName,
      cuisines: recipe.cuisines,
      cuisine: recipe.cuisine,
      dietaryRestrictions: recipe.dietaryRestrictions,
      diets: recipe.diets
    });
  }, [recipe]);

  // Handle cuisine from various formats with better type safety
  const cuisines = React.useMemo(() => {
    try {
      // Handle array case
      if (Array.isArray(recipe.cuisines)) {
        return recipe.cuisines
          .filter((c): c is string | number | boolean => c != null)
          .map(c => String(c).trim())
          .filter(c => c.length > 0);
      }
      
      // Handle string case
      if (typeof recipe.cuisines === 'string' && recipe.cuisines.trim()) {
        return recipe.cuisines
          .split(',')
          .map(c => c.trim())
          .filter(c => c.length > 0);
      }
      
      // Handle single cuisine field
      if (recipe.cuisine) {
        const cuisine = String(recipe.cuisine).trim();
        return cuisine ? [cuisine] : [];
      }
      
      // Try to extract from other potential fields
      const potentialCuisineFields = [
        recipe.cuisine,
        recipe.cuisineType?.[0],
        recipe.categories?.[0],
        recipe.tags?.find(t => typeof t === 'string' && t.length > 0)
      ];
      
      const foundCuisine = potentialCuisineFields
        .filter(Boolean)
        .map(String)
        .find(c => c.trim().length > 0);
        
      return foundCuisine ? [foundCuisine.trim()] : [];
    } catch (error) {
      console.error('Error processing cuisines:', error, recipe);
      return [];
    }
  }, [recipe]);
  
  // Handle dietary restrictions from various formats with normalization
  const dietaryRestrictions = React.useMemo(() => {
    try {
      const restrictions = new Set<string>();
      
      // Helper to add items to restrictions set
      const addRestrictions = (items: unknown) => {
        if (!items) return;
        
        // Handle array case
        if (Array.isArray(items)) {
          items.forEach(item => {
            if (item != null) {
              const str = String(item).trim().toLowerCase();
              if (str) restrictions.add(str);
            }
          });
          return;
        }
        
        // Handle string case (comma-separated)
        if (typeof items === 'string') {
          items.split(',')
            .map(s => s.trim().toLowerCase())
            .filter(Boolean)
            .forEach(s => restrictions.add(s));
        }
      };
      
      // Check all possible fields that might contain dietary info
      addRestrictions(recipe.dietaryRestrictions);
      addRestrictions(recipe.diets);
      addRestrictions(recipe.diets);
      addRestrictions(recipe.tags);
      
      // Also check healthLabels if it exists (common in some APIs)
      if (recipe.healthLabels && Array.isArray(recipe.healthLabels)) {
        const healthLabels = recipe.healthLabels
          .map(String)
          .map(s => s.toLowerCase())
          .filter(s => s.includes('free') || s.includes('diet') || s.includes('vegan') || s.includes('vegetarian'));
        healthLabels.forEach(label => restrictions.add(label));
      }
      
      // Normalize the values
      return Array.from(restrictions)
        .map(normalized => {
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
            case 'keto':
            case 'ketogenic':
              return 'keto';
            case 'paleo':
            case 'paleolithic':
              return 'paleo';
            case 'low carb':
            case 'low-carb':
              return 'low-carb';
            case 'high protein':
            case 'high-protein':
              return 'high-protein';
            default:
              return normalized;
          }
        })
        .filter(Boolean) // Remove any empty strings
        .filter((value, index, self) => self.indexOf(value) === index); // Remove duplicates
    } catch (error) {
      console.error('Error processing dietary restrictions:', error, recipe);
      return [];
    }
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
    <HoverCard>
      <HoverCardTrigger asChild>
        <div 
          className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer h-full flex flex-col"
          onClick={handleClick}
        >
          <Link to={getRecipePath()} onClick={(e) => e.stopPropagation()} className="flex flex-col h-full">
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
        
        <div className="p-4 flex-grow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {recipeName}
          </h3>
          
          {/* Cuisine Tags */}
          <div className="flex flex-wrap gap-2 mb-2">
            {/* Show only the first cuisine as the main tag */}
            {cuisines.length > 0 && (
              <span
                key={cuisines[0]}
                className="px-2.5 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full flex items-center"
              >
                <span className="mr-1">🌎</span>
                {cuisines[0].split(' ').map(word => 
                  word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                ).join(' ')}
              </span>
            )}
            
            {/* Show dietary restrictions as additional tags */}
            {dietaryRestrictions.length > 0 && dietaryRestrictions.map((diet) => {
              const getDietInfo = (d: string) => {
                switch(d.toLowerCase()) {
                  case 'vegetarian':
                    return { icon: '🥕', color: 'bg-green-100 text-green-800' };
                  case 'vegan':
                    return { icon: '🌱', color: 'bg-teal-100 text-teal-800' };
                  case 'gluten-free':
                    return { icon: '🌾', color: 'bg-amber-100 text-amber-800' };
                  case 'dairy-free':
                    return { icon: '🥛', color: 'bg-blue-100 text-blue-800' };
                  case 'keto':
                    return { icon: '🥑', color: 'bg-purple-100 text-purple-800' };
                  case 'paleo':
                    return { icon: '🥩', color: 'bg-red-100 text-red-800' };
                  default:
                    return { icon: '🍽️', color: 'bg-gray-100 text-gray-800' };
                }
              };
              
              const { icon, color } = getDietInfo(diet);
              
              return (
                <span 
                  key={diet} 
                  className={`px-2.5 py-1 text-xs font-medium rounded-full flex items-center ${color}`}
                  title={diet.split('-').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                  ).join(' ')}
                >
                  <span className="mr-1">{icon}</span>
                  {diet.split('-').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                  ).join('-')}
                </span>
              );
            })}
          </div>
          

          
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
      </HoverCardTrigger>
      
      <HoverCardContent className="w-80 p-0 overflow-hidden" align="start">
        <div className="p-4">
          <h4 className="font-semibold text-lg mb-2">{recipeName}</h4>
          
          {/* Description */}
          {recipe.description && (
            <p className="text-sm text-gray-600 mb-3 line-clamp-3">
              {recipe.description}
            </p>
          )}
          
          {/* Key Info */}
          <div className="space-y-2 text-sm">
            <div className="flex items-center text-gray-700">
              <Clock3 className="w-4 h-4 mr-2 text-gray-500" />
              <span>Prep: {recipe.prep_time || 'N/A'}</span>
            </div>
            <div className="flex items-center text-gray-700">
              <Utensils className="w-4 h-4 mr-2 text-gray-500" />
              <span>Cook: {recipe.cook_time || 'N/A'}</span>
            </div>
            <div className="flex items-center text-gray-700">
              <Users className="w-4 h-4 mr-2 text-gray-500" />
              <span>Servings: {recipe.servings || 'N/A'}</span>
            </div>
            {averageRating !== undefined && (
              <div className="flex items-center text-gray-700">
                <BarChart2 className="w-4 h-4 mr-2 text-gray-500" />
                <span>Rating: {Number(averageRating).toFixed(1)}/5</span>
              </div>
            )}
          </div>
          
          {/* Dietary Tags */}
          {(cuisines.length > 0 || dietaryRestrictions.length > 0) && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {cuisines.map((cuisine, idx) => (
                <span 
                  key={`cuisine-${idx}`}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                >
                  {cuisine}
                </span>
              ))}
              {dietaryRestrictions.map((diet, idx) => (
                <span 
                  key={`diet-${idx}`}
                  className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                >
                  {diet}
                </span>
              ))}
            </div>
          )}
        </div>
        
        {/* View Recipe Button */}
        <div className="bg-gray-50 px-4 py-3 border-t border-gray-100 text-right">
          <Link 
            to={getRecipePath()} 
            className="text-sm font-medium text-blue-600 hover:text-blue-800"
            onClick={(e) => e.stopPropagation()}
          >
            View Full Recipe →
          </Link>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
});

export default RecipeCard;
