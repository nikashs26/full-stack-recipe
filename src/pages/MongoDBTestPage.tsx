
import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Loader2, Database, AlertCircle, Check } from 'lucide-react';
import Header from '../components/Header';
import { checkMongoDBConnection, getDatabaseStatus } from '../utils/mongoStatus';
import { getAllRecipesFromDB, saveRecipeToDB } from '../lib/spoonacular';

const MongoDBTestPage: React.FC = () => {
  const [isChecking, setIsChecking] = useState(false);
  const [dbStatus, setDbStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown');
  const [recipeCount, setRecipeCount] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [testResult, setTestResult] = useState<string | null>(null);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    setIsChecking(true);
    setStatusMessage('Checking MongoDB connection...');
    
    try {
      const isConnected = await checkMongoDBConnection(2);
      setDbStatus(isConnected ? 'connected' : 'disconnected');
      
      if (isConnected) {
        const status = await getDatabaseStatus();
        setRecipeCount(status.recipeCount || 0);
        setStatusMessage(`Successfully connected to MongoDB. ${status.recipeCount || 0} recipes found.`);
      } else {
        setStatusMessage('Failed to connect to MongoDB. Check your connection string and network.');
      }
    } catch (error) {
      setDbStatus('disconnected');
      setStatusMessage(`Error checking MongoDB status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsChecking(false);
    }
  };

  const addTestRecipe = async () => {
    setIsTestRunning(true);
    setTestResult(null);
    
    try {
      const testRecipe = {
        id: `test-${Date.now()}`,
        title: `Test Recipe ${new Date().toLocaleTimeString()}`,
        cuisines: ["Test"],
        diets: ["vegetarian"],
        ingredients: ["test ingredient 1", "test ingredient 2"],
        instructions: ["Step 1: Test", "Step 2: Verify"],
        image: "https://via.placeholder.com/300",
        ratings: [5]
      };
      
      const result = await saveRecipeToDB(testRecipe);
      setTestResult(`Successfully added test recipe to MongoDB: ${JSON.stringify(result)}`);
      toast({
        title: "Test recipe added",
        description: "The test recipe was successfully saved to MongoDB",
      });
      
      // Refresh recipe count
      checkStatus();
    } catch (error) {
      setTestResult(`Error adding test recipe: ${error instanceof Error ? error.message : 'Unknown error'}`);
      toast({
        title: "Failed to add test recipe",
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive"
      });
    } finally {
      setIsTestRunning(false);
    }
  };

  const checkExistingRecipes = async () => {
    setIsTestRunning(true);
    setTestResult(null);
    
    try {
      const response = await getAllRecipesFromDB();
      
      if (response?.results && Array.isArray(response.results)) {
        const sampleRecipes = response.results.slice(0, 3).map(recipe => ({
          id: recipe.id,
          title: recipe.title || recipe.name
        }));
        
        setTestResult(`Found ${response.results.length} recipes in MongoDB. Sample: ${JSON.stringify(sampleRecipes, null, 2)}`);
      } else {
        setTestResult('No recipes found in MongoDB. The database might be empty.');
      }
    } catch (error) {
      setTestResult(`Error fetching recipes: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsTestRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">MongoDB Test Page</h1>
          <p className="text-gray-600">Use this page to test your MongoDB connection and operations</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Current MongoDB connection status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2 mb-4">
                {isChecking ? (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" /> Checking
                  </Badge>
                ) : dbStatus === 'connected' ? (
                  <Badge variant="outline" className="flex items-center gap-1 bg-green-50 text-green-700 border-green-200">
                    <Database className="h-3 w-3" /> Connected
                  </Badge>
                ) : dbStatus === 'disconnected' ? (
                  <Badge variant="outline" className="flex items-center gap-1 bg-red-50 text-red-700 border-red-200">
                    <AlertCircle className="h-3 w-3" /> Disconnected
                  </Badge>
                ) : (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Database className="h-3 w-3" /> Unknown
                  </Badge>
                )}
              </div>
              
              {recipeCount !== null && (
                <div className="mb-4">
                  <p className="text-sm font-medium">Recipe Count:</p>
                  <p className="text-2xl font-bold">{recipeCount}</p>
                </div>
              )}
              
              <Alert variant={dbStatus === 'connected' ? 'default' : 'destructive'} className="mt-2">
                <AlertTitle>Status</AlertTitle>
                <AlertDescription>{statusMessage}</AlertDescription>
              </Alert>
            </CardContent>
            <CardFooter>
              <Button 
                onClick={checkStatus}
                disabled={isChecking}
                variant="outline"
                className="w-full"
              >
                {isChecking && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Refresh Status
              </Button>
            </CardFooter>
          </Card>
          
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>MongoDB Tests</CardTitle>
              <CardDescription>Run tests to verify MongoDB operations</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="operations">
                <TabsList className="mb-4">
                  <TabsTrigger value="operations">Test Operations</TabsTrigger>
                  <TabsTrigger value="commands">MongoDB CLI Commands</TabsTrigger>
                </TabsList>
                
                <TabsContent value="operations" className="space-y-4">
                  <div className="space-y-2">
                    <p className="text-sm text-gray-500">Run operations to test MongoDB functionality</p>
                    
                    <div className="flex flex-wrap gap-2">
                      <Button 
                        onClick={addTestRecipe} 
                        disabled={isTestRunning || dbStatus !== 'connected'}
                        variant="default"
                      >
                        {isTestRunning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                        Add Test Recipe
                      </Button>
                      
                      <Button 
                        onClick={checkExistingRecipes}
                        disabled={isTestRunning || dbStatus !== 'connected'}
                        variant="outline"
                      >
                        {isTestRunning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                        Check Existing Recipes
                      </Button>
                    </div>
                  </div>
                  
                  {testResult && (
                    <>
                      <Separator />
                      <div className="mt-4">
                        <h3 className="text-sm font-medium mb-2">Test Result:</h3>
                        <pre className="bg-gray-100 p-3 rounded-md text-xs overflow-auto max-h-48">
                          {testResult}
                        </pre>
                      </div>
                    </>
                  )}
                </TabsContent>
                
                <TabsContent value="commands">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-1">Connect to MongoDB Atlas</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        mongo "mongodb+srv://betterbulkrecipes.mongodb.net/nikash" --username &lt;username&gt;
                      </pre>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium mb-1">List All Recipes</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        use nikash<br/>
                        db.Recipes.find().pretty()
                      </pre>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium mb-1">Insert a Test Recipe</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        db.Recipes.insertOne(&#123;<br/>
                        {"  id: 'test-123',\n  title: 'Test Recipe',\n  cuisines: ['Test'],\n  diets: ['vegetarian'],\n  ingredients: ['test ingredient']\n"}&#125;)
                      </pre>
                    </div>
                    
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>MongoDB Connection String</AlertTitle>
                      <AlertDescription>
                        Make sure your connection string in <code className="bg-gray-100 px-1 rounded">info.env</code> is correct:
                        <pre className="bg-gray-100 p-2 rounded-md text-xs mt-2">
                          MONGO_URI=mongodb+srv://&lt;username&gt;:&lt;password&gt;@betterbulkrecipes.mongodb.net/nikash?retryWrites=true&w=majority
                        </pre>
                      </AlertDescription>
                    </Alert>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default MongoDBTestPage;
