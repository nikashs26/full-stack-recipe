import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp, AlertTriangle, Check } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export interface MealPlannerSettings {
  targetCalories: number;
  targetProtein: number;
  targetCarbs: number;
  targetFat: number;
  includeSnacks: boolean;
}

interface MealPlannerAdvancedSettingsProps {
  settings: MealPlannerSettings;
  onSettingsChange: (settings: MealPlannerSettings) => void;
  isOpen: boolean;
  onToggle: (open: boolean) => void;
}

const MealPlannerAdvancedSettings: React.FC<MealPlannerAdvancedSettingsProps> = ({
  settings,
  onSettingsChange,
  isOpen,
  onToggle
}) => {
  const [tempSettings, setTempSettings] = useState<MealPlannerSettings>(settings);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [validationSuggestion, setValidationSuggestion] = useState<string | null>(null);

  // Update temp settings when props change
  useEffect(() => {
    setTempSettings(settings);
  }, [settings]);

  // Validate macros add up correctly (protein and carbs = 4 cal/g, fat = 9 cal/g)
  const validateMacros = (calories: number, protein: number, carbs: number, fat: number) => {
    const proteinCalories = protein * 4;
    const carbCalories = carbs * 4;
    const fatCalories = fat * 9;
    const totalMacroCalories = proteinCalories + carbCalories + fatCalories;
    
    const tolerance = 50; // Allow 50 calorie difference
    const diff = Math.abs(calories - totalMacroCalories);
    
    if (diff > tolerance) {
      const suggestedCalories = totalMacroCalories;
      return {
        isValid: false,
        error: `Macros don't add up! ${protein}g protein + ${carbs}g carbs + ${fat}g fat = ${totalMacroCalories} calories, but you entered ${calories} calories.`,
        suggestion: `Suggestion: Change calories to ${suggestedCalories} or adjust macros to match ${calories} calories.`
      };
    }
    
    return { isValid: true, error: null, suggestion: null };
  };

  // Calculate suggested macros based on calories
  const calculateSuggestedMacros = (calories: number) => {
    // Standard balanced macro distribution: 30% protein, 40% carbs, 30% fat
    const proteinCalories = calories * 0.30;
    const carbCalories = calories * 0.40;
    const fatCalories = calories * 0.30;
    
    return {
      protein: Math.round(proteinCalories / 4),
      carbs: Math.round(carbCalories / 4),
      fat: Math.round(fatCalories / 9)
    };
  };

  const handleInputChange = (field: keyof MealPlannerSettings, value: number | boolean) => {
    const newSettings = { ...tempSettings, [field]: value };
    setTempSettings(newSettings);
    
    // Validate if all macro fields are numbers
    if (typeof value === 'number') {
      const { targetCalories, targetProtein, targetCarbs, targetFat } = newSettings;
      const validation = validateMacros(targetCalories, targetProtein, targetCarbs, targetFat);
      setValidationError(validation.error);
      setValidationSuggestion(validation.suggestion);
    }
  };

  const handleApplySuggestion = () => {
    const suggested = calculateSuggestedMacros(tempSettings.targetCalories);
    const newSettings = {
      ...tempSettings,
      targetProtein: suggested.protein,
      targetCarbs: suggested.carbs,
      targetFat: suggested.fat
    };
    setTempSettings(newSettings);
    setValidationError(null);
    setValidationSuggestion(null);
  };

  const handleApplySettings = () => {
    const validation = validateMacros(
      tempSettings.targetCalories,
      tempSettings.targetProtein,
      tempSettings.targetCarbs,
      tempSettings.targetFat
    );
    
    if (validation.isValid) {
      onSettingsChange(tempSettings);
      setValidationError(null);
      setValidationSuggestion(null);
    } else {
      // Don't apply invalid settings
      setValidationError(validation.error);
      setValidationSuggestion(validation.suggestion);
    }
  };

  const handleReset = () => {
    // Reset to default values
    const defaultSettings: MealPlannerSettings = {
      targetCalories: 2000,
      targetProtein: 150,
      targetCarbs: 200,
      targetFat: 65,
      includeSnacks: false
    };
    setTempSettings(defaultSettings);
    setValidationError(null);
    setValidationSuggestion(null);
  };

  const isValid = !validationError;
  const hasChanges = JSON.stringify(tempSettings) !== JSON.stringify(settings);

  return (
    <Collapsible open={isOpen} onOpenChange={onToggle}>
      <CollapsibleTrigger asChild>
        <Button variant="outline" className="w-full justify-between mb-4">
          <span className="flex items-center gap-2">
            Advanced Settings
            {hasChanges && <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">Modified</span>}
          </span>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CollapsibleTrigger>
      
      <CollapsibleContent>
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Nutrition & Meal Customization</CardTitle>
            <CardDescription>
              Customize your daily calorie target, macronutrient distribution, and meal preferences for this meal plan.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Calories */}
            <div className="space-y-2">
              <Label htmlFor="calories">Daily Calories Target</Label>
              <Input
                id="calories"
                type="number"
                min="800"
                max="5000"
                step="50"
                value={tempSettings.targetCalories}
                onChange={(e) => handleInputChange('targetCalories', parseInt(e.target.value) || 0)}
                className="w-full"
              />
              <p className="text-xs text-gray-500">Recommended range: 1200-3000 calories</p>
            </div>

            {/* Macronutrients */}
            <div className="space-y-4">
              <h4 className="font-medium">Macronutrient Targets (grams per day)</h4>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="protein">Protein</Label>
                  <Input
                    id="protein"
                    type="number"
                    min="20"
                    max="400"
                    step="5"
                    value={tempSettings.targetProtein}
                    onChange={(e) => handleInputChange('targetProtein', parseInt(e.target.value) || 0)}
                  />
                  <p className="text-xs text-gray-500">{tempSettings.targetProtein * 4} cal</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="carbs">Carbohydrates</Label>
                  <Input
                    id="carbs"
                    type="number"
                    min="20"
                    max="500"
                    step="5"
                    value={tempSettings.targetCarbs}
                    onChange={(e) => handleInputChange('targetCarbs', parseInt(e.target.value) || 0)}
                  />
                  <p className="text-xs text-gray-500">{tempSettings.targetCarbs * 4} cal</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="fat">Fat</Label>
                  <Input
                    id="fat"
                    type="number"
                    min="10"
                    max="200"
                    step="5"
                    value={tempSettings.targetFat}
                    onChange={(e) => handleInputChange('targetFat', parseInt(e.target.value) || 0)}
                  />
                  <p className="text-xs text-gray-500">{tempSettings.targetFat * 9} cal</p>
                </div>
              </div>

              <div className="text-sm bg-gray-50 p-3 rounded">
                <strong>Total from macros:</strong> {(tempSettings.targetProtein * 4) + (tempSettings.targetCarbs * 4) + (tempSettings.targetFat * 9)} calories
              </div>
            </div>

            {/* Validation Messages */}
            {validationError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  {validationError}
                </AlertDescription>
              </Alert>
            )}

            {validationSuggestion && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="flex items-center justify-between">
                  <span>{validationSuggestion}</span>
                  <Button size="sm" onClick={handleApplySuggestion} className="ml-2">
                    Apply Suggestion
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {/* Snacks Toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label htmlFor="include-snacks">Include Snacks</Label>
                <p className="text-xs text-gray-500">Add healthy snacks between meals</p>
              </div>
              <Switch
                id="include-snacks"
                checked={tempSettings.includeSnacks}
                onCheckedChange={(checked) => handleInputChange('includeSnacks', checked)}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4 border-t">
              <Button 
                onClick={handleApplySettings} 
                disabled={!isValid}
                className="flex items-center gap-2"
              >
                {isValid && <Check className="h-4 w-4" />}
                Apply Settings
              </Button>
              <Button variant="outline" onClick={handleReset}>
                Reset to Defaults
              </Button>
              {hasChanges && (
                <Button 
                  variant="ghost" 
                  onClick={() => {
                    setTempSettings(settings);
                    setValidationError(null);
                    setValidationSuggestion(null);
                  }}
                >
                  Cancel Changes
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </CollapsibleContent>
    </Collapsible>
  );
};

export default MealPlannerAdvancedSettings;
