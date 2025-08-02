import React from 'react';
import { NutritionInfo } from '../types/recipe';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Flame, Droplet, Carrot, Zap, Scale, Users } from 'lucide-react';

interface RecipeNutritionProps {
  nutrition: NutritionInfo;
  servings?: number;
  className?: string;
  macrosPerServing?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

export const RecipeNutrition: React.FC<RecipeNutritionProps> = ({ 
  nutrition, 
  servings = 1,
  className = '',
  macrosPerServing
}) => {
  if (!nutrition && !macrosPerServing) return null;

  // Calculate per-serving values if serving size is provided
  const getPerServing = (value?: number) => {
    if (value === undefined) return 'N/A';
    const perServing = servings ? value / servings : value;
    return Math.round(perServing * 10) / 10;
  };

  // Use macrosPerServing if available, otherwise calculate from nutrition
  const getMacroValue = (macroType: 'calories' | 'protein' | 'carbs' | 'fat') => {
    if (macrosPerServing && macrosPerServing[macroType] !== undefined) {
      return macrosPerServing[macroType];
    }
    
    // Fallback to nutrition data
    switch (macroType) {
      case 'calories':
        return getPerServing(nutrition?.calories);
      case 'protein':
        return getPerServing(nutrition?.protein ? parseFloat(nutrition.protein) : undefined);
      case 'carbs':
        return getPerServing(nutrition?.carbohydrates ? parseFloat(nutrition.carbohydrates) : undefined);
      case 'fat':
        return getPerServing(nutrition?.fat ? parseFloat(nutrition.fat) : undefined);
      default:
        return 'N/A';
    }
  };

  const nutritionFacts = [
    { 
      name: 'Calories', 
      value: getMacroValue('calories'), 
      unit: 'kcal',
      icon: <Flame className="h-5 w-5 text-orange-500" />
    },
    { 
      name: 'Protein', 
      value: getMacroValue('protein'), 
      unit: 'g',
      icon: <Droplet className="h-5 w-5 text-blue-500" />
    },
    { 
      name: 'Carbs', 
      value: getMacroValue('carbs'), 
      unit: 'g',
      icon: <Carrot className="h-5 w-5 text-green-500" />
    },
    { 
      name: 'Fat', 
      value: getMacroValue('fat'), 
      unit: 'g',
      icon: <Droplet className="h-5 w-5 text-yellow-500" />
    },
    ...(nutrition?.fiber ? [{
      name: 'Fiber', 
      value: getPerServing(parseFloat(nutrition.fiber)), 
      unit: 'g',
      icon: <Zap className="h-5 w-5 text-purple-500" />
    }] : []),
    ...(nutrition?.sugar ? [{
      name: 'Sugar', 
      value: getPerServing(parseFloat(nutrition.sugar)), 
      unit: 'g',
      icon: <Scale className="h-5 w-5 text-pink-500" />
    }] : []),
    ...(nutrition?.sodium ? [{
      name: 'Sodium', 
      value: getPerServing(parseFloat(nutrition.sodium)), 
      unit: 'mg',
      icon: <Scale className="h-5 w-5 text-blue-300" />
    }] : [])
  ];

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Scale className="h-5 w-5 text-primary" />
          Nutrition Facts
          {servings > 1 && (
            <span className="text-sm font-normal text-muted-foreground ml-auto flex items-center">
              <Users className="h-3.5 w-3.5 mr-1" />
              Per Serving
            </span>
          )}
        </CardTitle>
        {nutrition?.servingSize && (
          <p className="text-sm text-muted-foreground">
            Serving Size: {nutrition.servingSize}
            {servings > 1 && ` • ${servings} servings total`}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {nutritionFacts.map((item, index) => (
            <div key={index} className="flex flex-col items-center p-3 bg-muted/30 rounded-lg">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-background mb-2">
                {item.icon}
              </div>
              <div className="text-center">
                <p className="font-medium">
                  {item.value} {item.unit}
                </p>
                <p className="text-xs text-muted-foreground">
                  {item.name}
                </p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Macro breakdown for better visualization */}
        {macrosPerServing && (
          <div className="mt-6 pt-4 border-t">
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Macro Breakdown</h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-blue-50 dark:bg-blue-950/20 rounded">
                <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {Math.round((macrosPerServing.protein * 4 / macrosPerServing.calories) * 100)}%
                </p>
                <p className="text-xs text-muted-foreground">Protein</p>
              </div>
              <div className="text-center p-2 bg-green-50 dark:bg-green-950/20 rounded">
                <p className="text-lg font-bold text-green-600 dark:text-green-400">
                  {Math.round((macrosPerServing.carbs * 4 / macrosPerServing.calories) * 100)}%
                </p>
                <p className="text-xs text-muted-foreground">Carbs</p>
              </div>
              <div className="text-center p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded">
                <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                  {Math.round((macrosPerServing.fat * 9 / macrosPerServing.calories) * 100)}%
                </p>
                <p className="text-xs text-muted-foreground">Fat</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RecipeNutrition;
