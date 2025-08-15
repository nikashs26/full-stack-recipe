
import React from 'react';
import { Link } from 'react-router-dom';
import { Clock, Star, Trash2, Clock3, Utensils, Users, BarChart2, Flame, Droplet, Carrot } from 'lucide-react';
import { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card';
import { ExtendedRecipe, Recipe } from '../types/recipe';
import { useRecipeClickTracking } from '../utils/clickTracking';
import { getReliableImageUrl } from '../utils/recipeUtils';
import { cleanRecipeDescription } from '../utils/recipeDescriptionCleaner';

interface RecipeCardProps {
  recipe: ExtendedRecipe | Recipe;
  isExternal?: boolean;
  onDelete?: (id: string | number) => void;
  onClick?: (recipe: ExtendedRecipe | Recipe) => void;
}

const RecipeCard: React.FC<RecipeCardProps> = React.memo(({ 
  recipe, 
  isExternal = false, 
  onDelete,
  onClick 
}) => {
  const { trackClick } = useRecipeClickTracking();

  // Handle recipe name from various sources
  const recipeName = React.useMemo(() => {
    if ('title' in recipe && recipe.title) return recipe.title;
    if ('name' in recipe && recipe.name) return recipe.name;
    return "Untitled Recipe";
  }, [recipe]);
  
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
          .filter((c): c is NonNullable<typeof c> => c != null)
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
      const cuisine = 'cuisine' in recipe ? recipe.cuisine : undefined;
      if (cuisine) {
        const cuisineStr = String(cuisine).trim();
        return cuisineStr ? [cuisineStr] : [];
      }
      
      // Handle cuisines from other potential fields
      const potentialCuisineFields = [
        'cuisineType' in recipe ? (recipe as any).cuisineType?.[0] : undefined,
        'categories' in recipe ? (recipe as any).categories?.[0] : undefined,
        'tags' in recipe ? (recipe as any).tags?.find((t: any) => typeof t === 'string' && t.length > 0) : undefined
      ].filter(Boolean);
      
      const foundCuisine = potentialCuisineFields
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
              if (str.length > 0) {
                restrictions.add(str);
              }
            }
          });
        }
        // Handle string case
        else if (typeof items === 'string') {
          const str = items.trim().toLowerCase();
          if (str.length > 0) {
            restrictions.add(str);
          }
        }
      };
      
      // Add restrictions from various possible fields
      addRestrictions(recipe.dietaryRestrictions);
      addRestrictions(recipe.diets);
      
      // Check for vegetarian/vegan flags in the recipe object
      if ('vegetarian' in recipe && (recipe as any).vegetarian) {
        restrictions.add('vegetarian');
      }
      if ('vegan' in recipe && (recipe as any).vegan) {
        restrictions.add('vegan');
      }
      
      return Array.from(restrictions);
    } catch (error) {
      console.error('Error processing dietary restrictions:', error, recipe);
      return [];
    }
  }, [recipe]);
  
  // Handle image from various sources with better fallback
  const imageUrl = React.useMemo((): string => {
    // Try different image sources in order of preference
    const imageSources = [
      recipe.image,
      recipe.imageUrl,
      (recipe as any).strMealThumb, // TheMealDB format
      (recipe as any).thumbnail
    ];
    
    for (const source of imageSources) {
      if (source) {
        // Use the original URL if it's not a broken pattern
        return getReliableImageUrl(source, 'medium');
      }
    }
    
    // Special handling for TheMealDB
    if ('source' in recipe && recipe.source === 'TheMealDB' && recipe.id) {
      const ingredientName = typeof recipe.id === 'string' ? recipe.id.split('_').pop() : '';
      return `https://www.themealdb.com/images/ingredients/${ingredientName || 'placeholder'}.jpg`;
    }
    
    // Return a reliable fallback image
    return getReliableImageUrl(undefined, 'medium');
  }, [recipe]);
  
  // Handle ID from various sources
  const recipeId = React.useMemo((): string => {
    if (recipe.id === null || recipe.id === undefined) return '';
    return String(recipe.id).replace('mealdb_', '');
  }, [recipe.id]);
  
  // Safely get readyInMinutes from either readyInMinutes or ready_in_minutes
  const readyInMinutes = React.useMemo(() => {
    if (recipe === null || typeof recipe !== 'object') return undefined;
    if ('readyInMinutes' in recipe && recipe.readyInMinutes !== undefined) return recipe.readyInMinutes;
    if ('ready_in_minutes' in recipe && recipe.ready_in_minutes !== undefined) return recipe.ready_in_minutes;
    return undefined;
  }, [recipe]);
  
  // Debug log for recipe data
  React.useEffect(() => {
    console.log('Recipe data in RecipeCard:', {
      id: recipe.id,
      title: recipeName,
      readyInMinutes,
      description: recipe.description,
      hasSummary: 'summary' in recipe,
      recipeType: recipe.type,
      readyInMinutesDirect: 'readyInMinutes' in recipe ? recipe.readyInMinutes : undefined,
      ready_in_minutesDirect: 'ready_in_minutes' in recipe ? (recipe as any).ready_in_minutes : undefined,
      // Add image debugging
      originalImage: recipe.image,
      originalImageUrl: (recipe as any).imageUrl,
      finalImageUrl: imageUrl,
      hasImage: !!recipe.image,
      hasImageUrl: !!(recipe as any).imageUrl
    });
  }, [recipe, recipeName, readyInMinutes, imageUrl]);
  
  // Calculate average rating if ratings is an array
  const averageRating = React.useMemo(() => {
    const getAverage = (value: unknown): number | undefined => {
      if (typeof value === 'number') {
        return value;
      }
      
      if (Array.isArray(value)) {
        // Handle array of numbers
        if (value.length > 0 && typeof value[0] === 'number') {
          const sum = (value as number[]).reduce((acc, score) => acc + score, 0);
          return sum / value.length;
        }
        
        // Handle array of rating objects
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
    
    // Try both rating and ratings properties
    const ratingValue = 'rating' in recipe ? recipe.rating : 'ratings' in recipe ? recipe.ratings : undefined;
    return getAverage(ratingValue);
  }, [recipe]);
  
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
    const path = isExternal ? `/external-recipe/${encodeURIComponent(id)}` : `/recipes/${id}`;
    console.log('RecipeCard routing:', { id, isExternal, path, recipeType: (recipe as any).type });
    return path;
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
          <Link 
            to={getRecipePath()} 
            onClick={(e) => {
              e.stopPropagation();
              // Track the recipe click
              const recipeType = isExternal ? 'external' : 'local';
              trackClick(String(recipe.id), recipeType);
            }} 
            className="flex flex-col h-full"
          >
        <div className="relative h-48 overflow-hidden">
          <img
            src={imageUrl}
            alt={recipeName}
            className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              // Use the utility function for fallback
              const fallbackImage = getReliableImageUrl(undefined, 'medium');
              if (target.src !== fallbackImage) {
                target.src = fallbackImage;
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
              <span>{readyInMinutes !== undefined ? `${readyInMinutes} min` : 'N/A'}</span>
            </div>
            <div className="flex items-center">
              <Star className="w-4 h-4 text-yellow-400 mr-1" />
              <span>{averageRating !== undefined ? Number(averageRating).toFixed(1) : 'N/A'}</span>
            </div>
          </div>
          
          {/* Macro Information */}
          {((recipe as any).macrosPerServing || recipe.nutrition) && (
            <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
              <div className="flex items-center space-x-2">
                <span className="flex items-center">
                  <Flame className="w-3 h-3 mr-1 text-orange-500" />
                  {((recipe as any).macrosPerServing?.calories || recipe.nutrition?.calories || 'N/A')} cal
                </span>
                <span className="flex items-center">
                  <Droplet className="w-3 h-3 mr-1 text-blue-500" />
                  {((recipe as any).macrosPerServing?.protein || recipe.nutrition?.protein || 'N/A')}g P
                </span>
                <span className="flex items-center">
                  <Carrot className="w-3 h-3 mr-1 text-green-500" />
                  {((recipe as any).macrosPerServing?.carbs || (recipe.nutrition as any)?.carbs || (recipe.nutrition as any)?.carbohydrates || 'N/A')}g C
                </span>
              </div>
              {recipe.servings && recipe.servings > 1 && (
                <span className="flex items-center">
                  <Users className="w-3 h-3 mr-1" />
                  {recipe.servings} servings
                </span>
              )}
            </div>
          )}
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
          {(recipe.description || ('summary' in recipe && (recipe as any).summary)) && (
            <p className="text-sm text-gray-600 mb-3 line-clamp-3">
              {cleanRecipeDescription(recipe.description || (recipe as any).summary)}
            </p>
          )}
          
          {/* Key Info */}
          <div className="space-y-2 text-sm">
            <div className="flex items-center text-gray-700">
              <Clock3 className="w-4 h-4 mr-2 text-gray-500" />
              <span>Prep: {'prepTime' in recipe ? recipe.prepTime : 'prep_time' in recipe ? (recipe as any).prep_time : 'N/A'}</span>
            </div>
            <div className="flex items-center text-gray-700">
              <Utensils className="w-4 h-4 mr-2 text-gray-500" />
              <span>Cook: {'cookTime' in recipe ? recipe.cookTime : 'cook_time' in recipe ? (recipe as any).cook_time : 'N/A'}</span>
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
