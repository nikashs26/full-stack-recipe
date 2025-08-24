import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '../utils/apiUtils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Calendar, 
  Clock, 
  ChefHat, 
  Eye, 
  Loader2, 
  RefreshCw, 
  TrendingUp,
  Utensils,
  AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';

interface MealPlanHistoryItem {
  id: string;
  generated_at: string;
  preferences_used: {
    favoriteCuisines?: string[];
    dietaryRestrictions?: string[];
    targetCalories?: number;
    targetProtein?: number;
  };
  meal_count: number;
  cuisines: string[];
  difficulties: string[];
  preview: string;
}

interface MealPlanHistoryProps {
  onSelectPlan?: (plan: any) => void;
  className?: string;
}

const MealPlanHistory: React.FC<MealPlanHistoryProps> = ({ 
  onSelectPlan, 
  className = '' 
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [history, setHistory] = useState<MealPlanHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    if (!user) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall('/api/meal-history');

      if (!response.ok) {
        // Get response text to debug what's actually being returned
        const responseText = await response.text();
        console.error('❌ API Response Error:', {
          status: response.status,
          statusText: response.statusText,
          responseText: responseText.substring(0, 200) + '...'
        });
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📥 Meal history API response:', data);
      
      if (data.success) {
        console.log('✅ Setting history data:', data.history);
        setHistory(data.history || []);
      } else {
        throw new Error(data.error || 'Failed to fetch meal history');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      toast({
        title: "Error",
        description: `Failed to load meal plan history: ${errorMessage}`,
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [user]);

  // Debug: Log history state changes
  useEffect(() => {
    console.log('🔄 History state updated:', history);
  }, [history]);

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy - h:mm a');
    } catch {
      return dateString;
    }
  };

  const handleViewPlan = async (planId: string) => {
    try {
      // Fetch the full meal plan details from the backend
      const response = await apiCall(`/api/meal-history/${planId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch meal plan details');
      }
      
      const data = await response.json();
      
      if (data.success && data.plan_details) {
        // Convert the backend format to the frontend format
        const mealPlan = {
          ...data.plan_details,
          days: data.plan_details.meal_plan ? Object.entries(data.plan_details.meal_plan).map(([day, meals]) => ({
            day: day.charAt(0).toUpperCase() + day.slice(1),
            meals: Object.entries(meals as any).map(([mealType, mealName]) => ({
              name: mealName as string,
              meal_type: mealType,
              cuisine: 'Unknown',
              difficulty: 'Unknown',
              prep_time: 'N/A',
              cook_time: 'N/A',
              servings: 'N/A'
            }))
          })) : []
        };
        
        if (onSelectPlan) {
          onSelectPlan(mealPlan);
        }
      } else {
        throw new Error(data.error || 'Failed to fetch meal plan details');
      }
    } catch (error) {
      console.error('Error fetching meal plan details:', error);
      toast({
        title: "Error",
        description: "Failed to load meal plan details. Please try again.",
        variant: "destructive"
      });
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            <CardTitle>Meal Plan History</CardTitle>
          </div>
          <CardDescription>
            Your previously generated meal plans
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span className="text-sm text-gray-600">Loading history...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            <CardTitle>Meal Plan History</CardTitle>
          </div>
          <CardDescription>
            Your previously generated meal plans
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mb-2" />
            <p className="text-sm text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchHistory} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (history.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            <CardTitle>Meal Plan History</CardTitle>
          </div>
          <CardDescription>
            Your previously generated meal plans
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <ChefHat className="h-8 w-8 text-gray-400 mb-2" />
            <p className="text-sm text-gray-600 mb-2">No meal plans generated yet</p>
            <p className="text-xs text-gray-500">
              Generate your first meal plan to see it here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            <div>
              <CardTitle>Meal Plan History</CardTitle>
              <CardDescription>
                {history.length} meal plan{history.length !== 1 ? 's' : ''} generated
              </CardDescription>
            </div>
          </div>
          <Button onClick={fetchHistory} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[400px]">
          <div className="p-6 space-y-4">
            {history.map((item, index) => (
              <div key={item.id} className="relative">
                <Card className="hover:shadow-md transition-shadow border-l-4 border-l-orange-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar className="h-4 w-4 text-gray-500" />
                          <span className="text-sm font-medium text-gray-900">
                            {formatDate(item.generated_at)}
                          </span>
                        </div>
                        
                        {/* Meal Stats */}
                        <div className="flex items-center gap-4 text-xs text-gray-600 mb-2">
                          <div className="flex items-center gap-1">
                            <Utensils className="h-3 w-3" />
                            <span>{item.meal_count} meals</span>
                          </div>
                          {item.preferences_used.targetCalories && (
                            <div className="flex items-center gap-1">
                              <TrendingUp className="h-3 w-3" />
                              <span>{item.preferences_used.targetCalories} cal</span>
                            </div>
                          )}
                        </div>

                        {/* Cuisines */}
                        {item.cuisines.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {item.cuisines.slice(0, 3).map((cuisine, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs px-2 py-0">
                                {cuisine}
                              </Badge>
                            ))}
                            {item.cuisines.length > 3 && (
                              <Badge variant="outline" className="text-xs px-2 py-0">
                                +{item.cuisines.length - 3} more
                              </Badge>
                            )}
                          </div>
                        )}

                        {/* Preview */}
                        <p className="text-xs text-gray-600 leading-relaxed">
                          {item.preview}
                        </p>
                      </div>

                      <Button
                        onClick={() => handleViewPlan(item.id)}
                        variant="outline"
                        size="sm"
                        className="ml-4 flex-shrink-0"
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        View
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                
                {index < history.length - 1 && (
                  <Separator className="my-4" />
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default MealPlanHistory;
