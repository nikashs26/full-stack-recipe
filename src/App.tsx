
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import RecipesPage from "./pages/RecipesPage";
import RecipeDetailPage from "./pages/RecipeDetailPage";
import ExternalRecipeDetailPage from "./pages/ExternalRecipeDetailPage";
import AddRecipePage from "./pages/AddRecipePage";
import EditRecipePage from "./pages/EditRecipePage";
import MongoDBTestPage from "./pages/MongoDBTestPage";
import NotFound from "./pages/NotFound";
import Footer from "./components/Footer";
import { Link } from "react-router-dom";
import { Database, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { checkMongoDBConnection } from "./utils/mongoStatus";

const queryClient = new QueryClient();

const App = () => {
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const isConnected = await checkMongoDBConnection();
        setDbStatus(isConnected ? 'connected' : 'disconnected');
      } catch (error) {
        console.error("Failed to check MongoDB connection:", error);
        setDbStatus('disconnected');
      }
    };
    
    checkConnection();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <div className="flex flex-col min-h-screen">
          <Toaster />
          <Sonner />
          <BrowserRouter>
            {/* MongoDB Status and Test Link */}
            <div className="fixed bottom-20 right-4 z-50 flex flex-col gap-2">
              <div className={`text-xs px-2 py-1 rounded-md flex items-center gap-1 ${
                dbStatus === 'connected' ? 'bg-green-100 text-green-800' : 
                dbStatus === 'disconnected' ? 'bg-red-100 text-red-800' : 
                'bg-yellow-100 text-yellow-800'
              }`}>
                {dbStatus === 'checking' && 'Checking MongoDB...'}
                {dbStatus === 'connected' && 'MongoDB Connected'}
                {dbStatus === 'disconnected' && 'MongoDB Disconnected'}
              </div>
              
              <Link 
                to="/mongodb-test" 
                className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-md shadow-md text-sm font-medium"
              >
                <Database className="h-4 w-4" />
                MongoDB Test
              </Link>
            </div>
            
            <Routes>
              <Route path="/" element={<RecipesPage />} />
              <Route path="/recipe/:id" element={<RecipeDetailPage />} />
              <Route path="/external-recipe/:id" element={<ExternalRecipeDetailPage />} />
              <Route path="/add-recipe" element={<AddRecipePage />} />
              <Route path="/edit-recipe/:id" element={<EditRecipePage />} />
              <Route path="/mongodb-test" element={<MongoDBTestPage />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
            <Footer />
          </BrowserRouter>
        </div>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
