
import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Loader2, Database, AlertCircle, Check, RefreshCcw, Wrench, Server } from 'lucide-react';
import Header from '../components/Header';
import { checkMongoDBConnection, getDatabaseStatus, testDirectConnection } from '../utils/mongoStatus';
import { getAllRecipesFromDB, saveRecipeToDB } from '../lib/spoonacular';

const MongoDBTestPage: React.FC = () => {
  const [isChecking, setIsChecking] = useState(false);
  const [dbStatus, setDbStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown');
  const [recipeCount, setRecipeCount] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [testResult, setTestResult] = useState<string | null>(null);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [mongoUri, setMongoUri] = useState<string>('');
  const [diagnosticData, setDiagnosticData] = useState<any>(null);
  const [isDiagnosticLoading, setIsDiagnosticLoading] = useState(false);
  const { toast } = useToast();

  // Load MongoDB URI from .env file on component mount
  useEffect(() => {
    const fetchEnv = async () => {
      try {
        const response = await fetch('/src/info.env');
        const text = await response.text();
        const uriMatch = text.match(/MONGO_URI=(.*)/);
        if (uriMatch && uriMatch[1]) {
          setMongoUri(uriMatch[1].trim());
        }
      } catch (error) {
        console.error("Could not load MongoDB URI from info.env", error);
      }
    };
    
    fetchEnv();
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

  const runDirectTest = async () => {
    setIsTestRunning(true);
    setTestResult(null);
    
    try {
      const result = await testDirectConnection();
      setTestResult(`Direct MongoDB connection test result: ${JSON.stringify(result, null, 2)}`);
      
      if (result.success) {
        toast({
          title: "MongoDB connection successful",
          description: result.message,
        });
      } else {
        toast({
          title: "MongoDB connection failed",
          description: result.message,
          variant: "destructive"
        });
      }
    } catch (error) {
      setTestResult(`Error running direct test: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsTestRunning(false);
    }
  };

  const getDiagnostics = async () => {
    setIsDiagnosticLoading(true);
    try {
      const response = await fetch('http://localhost:5000/mongodb-diagnostics');
      if (response.ok) {
        const data = await response.json();
        setDiagnosticData(data);
        
        // Check for DNS issues
        if (data.dns_check && !data.dns_check.success) {
          toast({
            title: "DNS Resolution Issue",
            description: data.dns_check.message,
            variant: "destructive"
          });
        }
      } else {
        toast({
          title: "Failed to get diagnostics",
          description: `Server returned ${response.status} ${response.statusText}`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error fetching diagnostics",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive"
      });
    } finally {
      setIsDiagnosticLoading(false);
    }
  };

  // Format diagnostic data for display
  const formatDiagnostics = () => {
    if (!diagnosticData) return null;
    
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium mb-1">Connection Information</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">Status:</span>{' '}
              {diagnosticData.mongodb_available ? (
                <Badge variant="outline" className="bg-green-50 text-green-700">Connected</Badge>
              ) : (
                <Badge variant="outline" className="bg-red-50 text-red-700">Disconnected</Badge>
              )}
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">Connection Type:</span>{' '}
              {diagnosticData.connection_string?.type || 'Unknown'}
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">URI Provided:</span>{' '}
              {diagnosticData.connection_string?.provided ? 'Yes' : 'No'}
            </div>
            {diagnosticData.database_info && (
              <>
                <div className="bg-gray-50 p-2 rounded">
                  <span className="font-medium">Database:</span>{' '}
                  {diagnosticData.database_info.database_name}
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <span className="font-medium">Collection:</span>{' '}
                  {diagnosticData.database_info.collection_name}
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <span className="font-medium">Recipe Count:</span>{' '}
                  {diagnosticData.database_info.document_count}
                </div>
              </>
            )}
          </div>
        </div>
        
        <div>
          <h3 className="text-sm font-medium mb-1">DNS Check Results</h3>
          <div className="bg-gray-50 p-3 rounded">
            <div className="flex items-center mb-2">
              <span className="font-medium mr-2">Status:</span>
              {diagnosticData.dns_check?.success ? (
                <Badge variant="outline" className="bg-green-50 text-green-700">Success</Badge>
              ) : (
                <Badge variant="outline" className="bg-red-50 text-red-700">Failed</Badge>
              )}
            </div>
            <p className="text-xs mb-2">
              <span className="font-medium">Message:</span>{' '}
              {diagnosticData.dns_check?.message || 'No message'}
            </p>
            {diagnosticData.dns_check?.ip && (
              <p className="text-xs">
                <span className="font-medium">IP Address:</span>{' '}
                {diagnosticData.dns_check.ip}
              </p>
            )}
            {diagnosticData.dns_check?.srv_count && (
              <p className="text-xs">
                <span className="font-medium">SRV Records:</span>{' '}
                {diagnosticData.dns_check.srv_count}
              </p>
            )}
          </div>
        </div>
        
        <div>
          <h3 className="text-sm font-medium mb-1">System Information</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">Python:</span>{' '}
              {diagnosticData.python_version?.split(' ')[0] || 'Unknown'}
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">PyMongo:</span>{' '}
              {diagnosticData.pymongo_version || 'Not installed'}
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">Platform:</span>{' '}
              {diagnosticData.platform || 'Unknown'}
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <span className="font-medium">Timestamp:</span>{' '}
              {diagnosticData.timestamp || 'Unknown'}
            </div>
          </div>
        </div>
      </div>
    );
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
                  <TabsTrigger value="connection">Connection Info</TabsTrigger>
                  <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
                  <TabsTrigger value="commands">MongoDB CLI</TabsTrigger>
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

                      <Button 
                        onClick={runDirectTest}
                        disabled={isTestRunning}
                        variant="outline"
                      >
                        {isTestRunning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Server className="mr-2 h-4 w-4" />}
                        Test Direct Connection
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
                
                <TabsContent value="connection" className="space-y-4">
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium">MongoDB Connection URI</h3>
                    <div className="flex gap-2">
                      <Input
                        value={mongoUri}
                        onChange={(e) => setMongoUri(e.target.value)}
                        className="font-mono text-xs"
                        placeholder="mongodb://hostname:port/dbname"
                      />
                      <Button variant="outline" className="shrink-0">
                        <RefreshCcw className="h-4 w-4 mr-2" /> Update
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      To update this permanently, modify the MONGO_URI in src/info.env
                    </p>
                  </div>
                  
                  <Alert>
                    <AlertTitle className="flex items-center gap-2">
                      <Database className="h-4 w-4" /> Connection Details
                    </AlertTitle>
                    <AlertDescription>
                      <div className="mt-2 space-y-1 text-xs">
                        <p><strong>Database:</strong> {mongoUri?.split('/').pop()?.split('?')[0] || 'recipes'}</p>
                        <p><strong>Collection:</strong> Recipes</p>
                        <p><strong>Connection Type:</strong> {mongoUri?.startsWith('mongodb+srv') ? 'MongoDB Atlas (SRV)' : 'Standard MongoDB'}</p>
                        <p><strong>Connection Status:</strong> {dbStatus === 'connected' ? 'Connected' : dbStatus === 'disconnected' ? 'Disconnected' : 'Unknown'}</p>
                      </div>
                    </AlertDescription>
                  </Alert>
                </TabsContent>

                <TabsContent value="diagnostics" className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-medium">MongoDB Diagnostics</h3>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={getDiagnostics}
                        disabled={isDiagnosticLoading}
                      >
                        {isDiagnosticLoading ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Wrench className="mr-2 h-4 w-4" />
                        )}
                        Run Diagnostics
                      </Button>
                    </div>
                    
                    {isDiagnosticLoading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      </div>
                    ) : diagnosticData ? (
                      formatDiagnostics()
                    ) : (
                      <div className="bg-gray-50 p-4 rounded text-center">
                        <p className="text-gray-500 text-sm">
                          Click "Run Diagnostics" to check your MongoDB connection
                        </p>
                      </div>
                    )}
                    
                    {diagnosticData && !diagnosticData.mongodb_available && (
                      <Alert variant="destructive" className="mt-4">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Connection Failed</AlertTitle>
                        <AlertDescription>
                          <div className="space-y-2 mt-2">
                            <p>Common MongoDB connection issues:</p>
                            <ul className="list-disc pl-5 text-sm space-y-1">
                              <li>Check that the MongoDB server is running</li>
                              <li>Verify your connection string is correct</li>
                              <li>Check network connectivity and firewalls</li>
                              <li>For MongoDB Atlas: Verify your IP is whitelisted</li>
                              <li>Ensure username and password are correct</li>
                              <li>For SRV records: Verify DNS resolution is working</li>
                            </ul>
                          </div>
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </TabsContent>
                
                <TabsContent value="commands">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-1">Connect to MongoDB</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        {mongoUri.startsWith('mongodb+srv') ? 
                          `mongo "${mongoUri}"` : 
                          `mongo --host ${mongoUri.replace('mongodb://', '').split('/')[0]}`}
                      </pre>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium mb-1">List All Recipes</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        use {mongoUri?.split('/').pop()?.split('?')[0] || 'recipes'}<br/>
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
                    
                    <div>
                      <h3 className="text-sm font-medium mb-1">Check MongoDB Status</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        db.serverStatus()
                      </pre>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium mb-1">Check DNS Resolution</h3>
                      <pre className="bg-gray-100 p-2 rounded-md text-xs">
                        # On Linux/Mac<br/>
                        nslookup {mongoUri.includes('@') ? mongoUri.split('@')[1].split('/')[0] : 
                                 mongoUri.includes('://') ? mongoUri.split('://')[1].split('/')[0] : 
                                 'your-mongodb-host'}<br/><br/>
                        # For SRV records<br/>
                        nslookup -type=SRV _mongodb._tcp.{mongoUri.includes('@') ? 
                                              mongoUri.split('@')[1].split('/')[0] : 
                                              'your-mongodb-host'}
                      </pre>
                    </div>
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
