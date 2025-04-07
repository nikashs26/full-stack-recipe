
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, Code, Database, Copy } from 'lucide-react';
import { addTestRecipeToDB, checkRecipesInDB, getMongoCLICommands } from '@/utils/dbTest';
import { useToast } from '@/hooks/use-toast';

const MongoDBTester: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<{
    success?: boolean;
    message?: string;
    count?: number;
    recipes?: any[];
  } | null>(null);
  const [showCommandLine, setShowCommandLine] = useState<boolean>(false);
  const { toast } = useToast();

  const handleAddTestRecipe = async () => {
    setLoading(true);
    try {
      const result = await addTestRecipeToDB();
      setResult(result);
      
      if (result.success) {
        toast({
          title: "Test Recipe Added",
          description: result.message,
        });
      } else {
        toast({
          title: "Failed to Add Test Recipe",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error in add test:", error);
      setResult({
        success: false,
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
      
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCheckRecipes = async () => {
    setLoading(true);
    try {
      const result = await checkRecipesInDB();
      setResult(result);
      
      if (result.success) {
        toast({
          title: "MongoDB Check Complete",
          description: result.message,
        });
      } else {
        toast({
          title: "MongoDB Check Failed",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error in check recipes:", error);
      setResult({
        success: false,
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
      
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCommands = () => {
    navigator.clipboard.writeText(getMongoCLICommands());
    toast({
      title: "Copied",
      description: "MongoDB CLI commands copied to clipboard",
    });
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" /> 
          MongoDB Test Tools
        </CardTitle>
        <CardDescription>
          Test your MongoDB connection and add sample recipes directly to the database
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-4">
            <Button 
              onClick={handleAddTestRecipe} 
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? "Adding..." : "Add Test Recipe to MongoDB"}
            </Button>
            
            <Button 
              onClick={handleCheckRecipes} 
              variant="outline" 
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? "Checking..." : "Check MongoDB Recipes"}
            </Button>

            <Button 
              onClick={() => setShowCommandLine(!showCommandLine)} 
              variant="secondary"
              className="flex items-center gap-2"
            >
              <Code className="h-4 w-4" />
              {showCommandLine ? "Hide CLI Commands" : "Show CLI Commands"}
            </Button>
          </div>
          
          {result && (
            <Alert variant={result.success ? "default" : "destructive"}>
              {result.success ? 
                <CheckCircle className="h-4 w-4" /> : 
                <AlertCircle className="h-4 w-4" />
              }
              <AlertTitle>{result.success ? "Success" : "Error"}</AlertTitle>
              <AlertDescription>{result.message}</AlertDescription>
            </Alert>
          )}
          
          {result?.recipes && result.recipes.length > 0 && (
            <div className="mt-4 border rounded-md p-4 bg-gray-50">
              <h3 className="font-medium mb-2">Found {result.recipes.length} recipes:</h3>
              <div className="max-h-60 overflow-y-auto">
                <ul className="space-y-2">
                  {result.recipes.map((recipe, index) => (
                    <li key={index} className="p-2 bg-white border rounded-md">
                      <strong>{recipe.title || recipe.name || "Untitled"}</strong>
                      <span className="text-sm text-gray-500"> (ID: {recipe.id || recipe._id})</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          
          {showCommandLine && (
            <div className="mt-4 border rounded-md bg-gray-900 text-gray-100 p-4 relative">
              <div className="absolute top-2 right-2">
                <Button variant="ghost" size="sm" onClick={handleCopyCommands} className="h-8 text-gray-300 hover:text-white">
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                {getMongoCLICommands()}
              </pre>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between text-sm text-gray-500">
        <p>Make sure your Python backend is running on port 5000</p>
      </CardFooter>
    </Card>
  );
};

export default MongoDBTester;
