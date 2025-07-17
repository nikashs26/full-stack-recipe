import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles, TrendingUp, Leaf, Star, ChefHat } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface AIRecipe {
  id: string;
  title: string;
  summary: string;
  cuisine: string[];
  diets: string[];
  readyInMinutes: number;
  servings: number;
  difficulty: string;
  ingredients: Array<{
    name: string;
    amount: string;
    unit: string;
  }>;
  instructions: string[];
  nutritionalHighlights: string[];
  tags: string[];
  source: string;
  generatedAt: string;
  generationType: string;
  image: string;
}

interface AIRecipeGeneratorProps {
  onRecipeGenerated?: (recipe: AIRecipe) => void;
}

const AIRecipeGenerator: React.FC<AIRecipeGeneratorProps> = ({ onRecipeGenerated }) => {
  const [selectedType, setSelectedType] = useState<'trending' | 'seasonal' | 'personalized' | 'search'>('trending');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRecipes, setGeneratedRecipes] = useState<AIRecipe[]>([]);
  const { toast } = useToast();

  // Fetch trending topics for user guidance
  const { data: trendingData } = useQuery({
    queryKey: ['trending-topics'],
    queryFn: async () => {
      const response = await fetch('/api/ai-recipes/trending-topics');
      if (!response.ok) throw new Error('Failed to fetch trending topics');
      return response.json();
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
  });

  const generateRecipes = async (type: string, count: number = 6) => {
    setIsGenerating(true);
    try {
      let response;
      
      switch (type) {
        case 'trending':
          response = await fetch(`/api/ai-recipes/trending?count=${count}`);
          break;
        case 'seasonal':
          response = await fetch(`/api/ai-recipes/seasonal?count=${count}`);
          break;
        case 'personalized':
          response = await fetch(`/api/ai-recipes/personalized?count=${count}`);
          break;
        case 'recommendations':
          response = await fetch(`/api/ai-recipes/recommendations?count=${count}`);
          break;
        default:
          throw new Error('Invalid recipe type');
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate recipes');
      }

      const data = await response.json();
      
      if (data.success && data.recipes) {
        setGeneratedRecipes(data.recipes);
        toast({
          title: "Recipes Generated! ✨",
          description: `Generated ${data.recipes.length} fresh ${type} recipes using AI`,
        });
        
        // Notify parent component if callback provided
        if (onRecipeGenerated && data.recipes.length > 0) {
          onRecipeGenerated(data.recipes[0]);
        }
      } else {
        throw new Error(data.error || 'No recipes generated');
      }
    } catch (error) {
      console.error('Recipe generation error:', error);
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : "Failed to generate recipes. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'trending': return <TrendingUp className="h-4 w-4" />;
      case 'seasonal': return <Leaf className="h-4 w-4" />;
      case 'personalized': return <Star className="h-4 w-4" />;
      default: return <ChefHat className="h-4 w-4" />;
    }
  };

  const getGenerationTypeColor = (type: string) => {
    switch (type) {
      case 'trend_based': return 'bg-orange-100 text-orange-800';
      case 'seasonal': return 'bg-green-100 text-green-800';
      case 'personalized': return 'bg-purple-100 text-purple-800';
      case 'cuisine_based': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Generator Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            AI Recipe Generator
          </CardTitle>
          <CardDescription>
            Generate fresh, diverse recipes using AI instead of seeing the same hardcoded recipes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Recipe Type Selection */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { type: 'trending', label: 'Trending', desc: 'Based on food trends' },
              { type: 'seasonal', label: 'Seasonal', desc: 'Current season ingredients' },
              { type: 'personalized', label: 'Personal', desc: 'Your preferences' },
              { type: 'recommendations', label: 'Smart', desc: 'AI recommendations' }
            ].map(({ type, label, desc }) => (
              <Button
                key={type}
                variant={selectedType === type ? "default" : "outline"}
                onClick={() => setSelectedType(type as any)}
                className="flex flex-col items-center gap-1 h-auto py-3"
                disabled={isGenerating}
              >
                {getTypeIcon(type)}
                <span className="text-sm font-medium">{label}</span>
                <span className="text-xs text-muted-foreground">{desc}</span>
              </Button>
            ))}
          </div>

          {/* Generate Button */}
          <Button 
            onClick={() => generateRecipes(selectedType)} 
            disabled={isGenerating}
            size="lg"
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating Fresh Recipes...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate {selectedType} Recipes
              </>
            )}
          </Button>

          {/* Trending Topics Display */}
          {trendingData?.success && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Current Trending Topics:</h4>
              <div className="flex flex-wrap gap-2">
                {trendingData.trending_topics.slice(0, 6).map((topic: string, index: number) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generated Recipes Display */}
      {generatedRecipes.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            ✨ Fresh AI-Generated Recipes ({generatedRecipes.length})
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {generatedRecipes.map((recipe) => (
              <Card key={recipe.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                <div className="aspect-video bg-gradient-to-br from-orange-100 to-red-100 relative">
                  <img 
                    src={recipe.image} 
                    alt={recipe.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400';
                    }}
                  />
                  <div className="absolute top-2 left-2">
                    <Badge className={getGenerationTypeColor(recipe.generationType)}>
                      AI: {recipe.generationType.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div className="absolute top-2 right-2">
                    <Badge variant="secondary">
                      {recipe.readyInMinutes}min
                    </Badge>
                  </div>
                </div>
                
                <CardContent className="p-4">
                  <h4 className="font-semibold text-sm mb-2 line-clamp-2">{recipe.title}</h4>
                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">{recipe.summary}</p>
                  
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-1">
                      {recipe.cuisine.slice(0, 2).map((cuisine, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {cuisine}
                        </Badge>
                      ))}
                      {recipe.diets.slice(0, 1).map((diet, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {diet}
                        </Badge>
                      ))}
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Serves {recipe.servings}</span>
                      <span>{recipe.difficulty}</span>
                    </div>
                    
                    {recipe.nutritionalHighlights.length > 0 && (
                      <div className="text-xs text-green-600">
                        💚 {recipe.nutritionalHighlights.slice(0, 2).join(', ')}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {generatedRecipes.length === 0 && !isGenerating && (
        <Card className="text-center py-8">
          <CardContent>
            <Sparkles className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Ready to Generate Fresh Recipes?
            </h3>
            <p className="text-gray-600 mb-4">
              Click "Generate" to create diverse, AI-powered recipes instead of seeing the same hardcoded ones!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AIRecipeGenerator; 