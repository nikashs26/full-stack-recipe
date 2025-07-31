import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Utensils, Apple, Carrot, Coffee, Salad, GlassWater } from 'lucide-react';
import type { NutritionSummary as NutritionSummaryType } from '@/services/mealPlannerService';

interface NutritionCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  progress?: number;
  target?: number;
  unit?: string;
}

const NutritionCard: React.FC<NutritionCardProps> = ({ title, value, icon, progress, target, unit = '' }) => (
  <Card className="flex-1 min-w-[150px] h-full">
    <CardContent className="p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <div className="text-primary">{icon}</div>
      </div>
      <div className="text-2xl font-bold">
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
      </div>
      {progress !== undefined && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            {target !== undefined && <span>{Math.round(progress)}% of {target.toLocaleString()}{unit}</span>}
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}
    </CardContent>
  </Card>
);

interface NutritionalSummaryProps {
  nutrition: NutritionSummaryType;
  className?: string;
}

export const NutritionalSummary: React.FC<NutritionalSummaryProps> = ({ nutrition, className = '' }) => {
  if (!nutrition) return null;

  const { daily_average, weekly_totals, targets, meal_inclusions } = nutrition;

  // Helper to get numeric value from NutritionField
  const getNumericValue = (value: any): number => {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') return parseFloat(value) || 0;
    if (value && typeof value === 'object' && 'amount' in value) {
      return typeof value.amount === 'number' ? value.amount : parseFloat(value.amount) || 0;
    }
    return 0;
  };

  const dailyCalories = getNumericValue(daily_average?.calories || 0);
  const dailyProtein = getNumericValue(daily_average?.protein || 0);
  const dailyCarbs = getNumericValue(daily_average?.carbs || 0);
  const dailyFat = getNumericValue(daily_average?.fat || 0);

  const targetCalories = getNumericValue(targets?.calories || 2000);
  const targetProtein = getNumericValue(targets?.protein || 150);
  const targetCarbs = getNumericValue(targets?.carbs || 200);
  const targetFat = getNumericValue(targets?.fat || 65);

  return (
    <div className={`space-y-6 ${className}`}>
      <h3 className="text-xl font-bold">Nutritional Summary</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Daily Averages */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Daily Averages</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <NutritionCard 
              title="Calories" 
              value={dailyCalories} 
              icon={<GlassWater className="h-4 w-4" />}
              progress={targetCalories ? (dailyCalories / targetCalories) * 100 : undefined}
              target={targetCalories}
            />
            
            <div className="grid grid-cols-3 gap-4">
              <NutritionCard 
                title="Protein" 
                value={dailyProtein} 
                icon={<Carrot className="h-4 w-4" />}
                unit="g"
                progress={targetProtein ? (dailyProtein / targetProtein) * 100 : undefined}
                target={targetProtein}
              />
              <NutritionCard 
                title="Carbs" 
                value={dailyCarbs} 
                icon={<Apple className="h-4 w-4" />}
                unit="g"
                progress={targetCarbs ? (dailyCarbs / targetCarbs) * 100 : undefined}
                target={targetCarbs}
              />
              <NutritionCard 
                title="Fat" 
                value={dailyFat} 
                icon={<Utensils className="h-4 w-4" />}
                unit="g"
                progress={targetFat ? (dailyFat / targetFat) * 100 : undefined}
                target={targetFat}
              />
            </div>
          </CardContent>
        </Card>

        {/* Weekly Totals */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Weekly Totals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <NutritionCard 
                title="Calories" 
                value={getNumericValue(weekly_totals?.calories || 0)} 
                icon={<GlassWater className="h-4 w-4" />}
              />
              <NutritionCard 
                title="Protein" 
                value={getNumericValue(weekly_totals?.protein || 0)} 
                icon={<Carrot className="h-4 w-4" />}
                unit="g"
              />
              <NutritionCard 
                title="Carbs" 
                value={getNumericValue(weekly_totals?.carbs || 0)} 
                icon={<Apple className="h-4 w-4" />}
                unit="g"
              />
              <NutritionCard 
                title="Fat" 
                value={getNumericValue(weekly_totals?.fat || 0)} 
                icon={<Utensils className="h-4 w-4" />}
                unit="g"
              />
            </div>

            {/* Meal Inclusions */}
            {meal_inclusions && (
              <div className="mt-6">
                <h4 className="font-medium mb-3">Meal Inclusions</h4>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(meal_inclusions).map(([mealType, included]) => (
                    included && (
                      <div key={mealType} className="flex items-center space-x-2 bg-gray-50 p-3 rounded-lg">
                        {mealType === 'breakfast' && <Coffee className="h-4 w-4 text-amber-500" />}
                        {mealType === 'lunch' && <Salad className="h-4 w-4 text-green-500" />}
                        {mealType === 'dinner' && <Utensils className="h-4 w-4 text-blue-500" />}
                        {mealType === 'snacks' && <Apple className="h-4 w-4 text-red-500" />}
                        <span className="capitalize text-sm font-medium">{mealType}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NutritionalSummary;
