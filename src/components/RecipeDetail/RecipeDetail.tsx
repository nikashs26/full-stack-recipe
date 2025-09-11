import React from 'react';
import { Recipe } from '../../types/recipe';
import { Clock, Utensils, ChefHat, Users, Info, Timer, Clock3, Salad, Carrot, Wheat, Zap } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RecipeNutrition } from '../RecipeNutrition';
import { getReliableImageUrl } from '../../utils/recipeUtils';

interface RecipeDetailProps {
  recipe: Recipe;
  onAddToFavorites: () => void;
  onAddToShoppingList: () => void;
  onAssignToFolder: () => void;
  isFavorite: boolean;
  currentFolder?: { name: string };
  avgRating: number;
  reviewCount: number;
}

export const RecipeDetail: React.FC<RecipeDetailProps> = ({
  recipe,
  onAddToFavorites,
  onAddToShoppingList,
  onAssignToFolder,
  isFavorite,
  currentFolder,
  avgRating,
  reviewCount
}) => {
  // Format time in minutes to human-readable format
  const formatTime = (minutes?: number) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins > 0 ? `${mins}m` : ''}`.trim();
    }
    return `${mins}m`;
  };

  // Format dietary restrictions as badges
  const renderDietaryRestrictions = () => {
    if (!recipe.dietaryRestrictions?.length) return null;
    
    const restrictionIcons: Record<string, JSX.Element> = {
      'vegetarian': <Salad className="w-4 h-4 mr-1" />,
      'vegan': <Carrot className="w-4 h-4 mr-1" />,
      'gluten-free': <Wheat className="w-4 h-4 mr-1" />,
      'keto': <Zap className="w-4 h-4 mr-1" />
    };

    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {recipe.dietaryRestrictions.map((restriction) => (
          <Badge key={restriction} variant="secondary" className="flex items-center">
            {restrictionIcons[restriction]}
            {restriction}
          </Badge>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Recipe Header */}
      <div className="relative rounded-xl overflow-hidden bg-muted">
        <div className="aspect-w-16 aspect-h-9 w-full">
          <img
            src={getReliableImageUrl(recipe.image, 'large')}
            alt={recipe.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = getReliableImageUrl(undefined, 'large');
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
          
          <div className="absolute bottom-0 left-0 right-0 p-6 md:p-8">
            <div className="max-w-4xl mx-auto">
              <div className="flex flex-wrap gap-2 mb-3">
                <Badge variant="secondary" className="bg-white/20 backdrop-blur-sm text-white border-none">
                  <Utensils className="h-3.5 w-3.5 mr-1.5" />
                  {recipe.cuisine || 'Recipe'}
                </Badge>
                {recipe.difficulty && (
                  <Badge variant="secondary" className="bg-white/20 backdrop-blur-sm text-white border-none">
                    <ChefHat className="h-3.5 w-3.5 mr-1.5" />
                    {recipe.difficulty}
                  </Badge>
                )}
              </div>
              
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4 drop-shadow-lg">
                {recipe.name}
              </h1>
              
              {(recipe.description || recipe.dietaryRestrictions?.length) && (
                <div className="mt-4 text-white/90">
                  {recipe.description && (
                    <p className="text-base md:text-lg mb-3">{recipe.description}</p>
                  )}
                  {renderDietaryRestrictions()}
                </div>
              )}
              
              <div className="flex flex-wrap items-center gap-3 mt-6 text-sm">
                {recipe.prepTime && (
                  <div className="flex items-center bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full text-white">
                    <Timer className="h-4 w-4 mr-1.5" />
                    Prep: {formatTime(recipe.prepTime)}
                  </div>
                )}
                {recipe.cookTime && (
                  <div className="flex items-center bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full text-white">
                    <Clock3 className="h-4 w-4 mr-1.5" />
                    Cook: {formatTime(recipe.cookTime)}
                  </div>
                )}
                {recipe.servings && (
                  <div className="flex items-center bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full text-white">
                    <Users className="h-4 w-4 mr-1.5" />
                    {recipe.servings} {recipe.servings === 1 ? 'serving' : 'servings'}
                  </div>
                )}
                {avgRating > 0 && (
                  <div className="flex items-center bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full text-white">
                    <Star className="h-4 w-4 text-yellow-400 fill-yellow-400 mr-1.5" />
                    {avgRating} ({reviewCount})
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Ingredients */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Utensils className="h-5 w-5 text-primary" />
                Ingredients
                {recipe.servings && recipe.servings > 1 && (
                  <span className="text-sm font-normal text-muted-foreground ml-auto">
                    Serves {recipe.servings}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {recipe.ingredients?.length > 0 ? (
                  recipe.ingredients.map((ingredient, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary/10 text-primary text-xs mt-0.5 flex-shrink-0">
                        {index + 1}
                      </span>
                      <span className="text-sm">
                        {typeof ingredient === 'string' ? (
                          ingredient
                        ) : (
                          <>
                            {ingredient.amount && <span className="font-medium">{ingredient.amount} </span>}
                            {ingredient.unit && <span className="text-muted-foreground">{ingredient.unit} </span>}
                            <span>{ingredient.name}</span>
                          </>
                        )}
                      </span>
                    </li>
                  ))
                ) : (
                  <li className="text-muted-foreground text-sm">No ingredients listed</li>
                )}
              </ul>
            </CardContent>
          </Card>

          {/* Nutrition Facts */}
          {(recipe.nutrition || (recipe as any).macrosPerServing) && (
            <div className="mt-6">
              <RecipeNutrition 
                nutrition={recipe.nutrition} 
                servings={recipe.servings}
                macrosPerServing={(recipe as any).macrosPerServing}
              />
            </div>
          )}
        </div>

        {/* Right Column - Instructions */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <ChefHat className="h-5 w-5 text-primary" />
                Instructions
                {recipe.totalTime && (
                  <span className="text-sm font-normal text-muted-foreground ml-auto flex items-center">
                    <Clock className="h-3.5 w-3.5 mr-1.5" />
                    {formatTime(recipe.totalTime)}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {recipe.instructions?.length > 0 ? (
                  recipe.instructions.map((step, index) => (
                    <div key={index} className="flex group">
                      <div className="flex-shrink-0">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-medium text-sm mr-4 mt-0.5 group-hover:bg-primary/20 transition-colors">
                          {index + 1}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0 pb-6 border-b border-muted last:border-0 last:pb-0">
                        <p className="text-foreground">
                          {step.endsWith('.') ? step : `${step}.`}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <Info className="h-5 w-5 text-yellow-400" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700">
                          No detailed instructions available for this recipe.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Source Attribution */}
          {recipe.source && (
            <div className="mt-6 text-sm text-muted-foreground">
              <p className="flex items-center">
                <Info className="h-4 w-4 mr-2 flex-shrink-0" />
                {recipe.sourceUrl ? (
                  <span>
                    Recipe from{' '}
                    <a 
                      href={recipe.sourceUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      {recipe.source}
                    </a>
                  </span>
                ) : (
                  <span>Source: {recipe.source}</span>
                )}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecipeDetail;
