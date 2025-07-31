import React from 'react';
import { NutritionInfo } from '../types/recipe';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Flame, Droplet, Carrot, Zap, Scale } from 'lucide-react';

interface RecipeNutritionProps {
  nutrition: NutritionInfo;
  servings?: number;
  className?: string;
}

export const RecipeNutrition: React.FC<RecipeNutritionProps> = ({ 
  nutrition, 
  servings = 1,
  className = ''
}) => {
  if (!nutrition) return null;

  // Calculate per-serving values if serving size is provided
  const getPerServing = (value?: number) => {
    if (value === undefined) return 'N/A';
    const perServing = servings ? value / servings : value;
    return Math.round(perServing * 10) / 10;
  };

  const nutritionFacts = [
    { 
      name: 'Calories', 
      value: getPerServing(nutrition.calories), 
      unit: 'kcal',
      icon: <Flame className="h-5 w-5 text-orange-500" />
    },
    { 
      name: 'Protein', 
      value: getPerServing(nutrition.protein ? parseFloat(nutrition.protein) : undefined), 
      unit: 'g',
      icon: <Droplet className="h-5 w-5 text-blue-500" />
    },
    { 
      name: 'Carbs', 
      value: getPerServing(nutrition.carbohydrates ? parseFloat(nutrition.carbohydrates) : undefined), 
      unit: 'g',
      icon: <Carrot className="h-5 w-5 text-green-500" />
    },
    { 
      name: 'Fat', 
      value: getPerServing(nutrition.fat ? parseFloat(nutrition.fat) : undefined), 
      unit: 'g',
      icon: <Droplet className="h-5 w-5 text-yellow-500" />
    },
    ...(nutrition.fiber ? [{
      name: 'Fiber', 
      value: getPerServing(parseFloat(nutrition.fiber)), 
      unit: 'g',
      icon: <Zap className="h-5 w-5 text-purple-500" />
    }] : []),
    ...(nutrition.sugar ? [{
      name: 'Sugar', 
      value: getPerServing(parseFloat(nutrition.sugar)), 
      unit: 'g',
      icon: <Scale className="h-5 w-5 text-pink-500" />
    }] : []),
    ...(nutrition.sodium ? [{
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
        </CardTitle>
        {nutrition.servingSize && (
          <p className="text-sm text-muted-foreground">
            Serving Size: {nutrition.servingSize}
            {servings > 1 && ` • ${servings} servings`}
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
      </CardContent>
    </Card>
  );
};

export default RecipeNutrition;
