
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import SimplifiedRecipesPage from "./pages/SimplifiedRecipesPage";
import RecipeDetailPage from "./pages/RecipeDetailPage";
import ExternalRecipeDetailPage from "./pages/ExternalRecipeDetailPage";
import AddRecipePage from "./pages/AddRecipePage";
import EditRecipePage from "./pages/EditRecipePage";
import MongoDBTestPage from "./pages/MongoDBTestPage";
import NotFound from "./pages/NotFound";
import Footer from "./components/Footer";
import HomePage from "./pages/HomePage";
import FoldersPage from "./pages/FoldersPage";
import FavoritesPage from "./pages/FavoritesPage";
import ShoppingListPage from "./pages/ShoppingListPage";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";
import UserPreferencesPage from "./pages/UserPreferencesPage";
import { Link } from "react-router-dom";
import { Database } from "lucide-react";
import { AuthProvider } from "./context/SimpleAuthContext";
import ManualRecipeDetailPage from "./pages/ManualRecipeDetailPage";

const queryClient = new QueryClient();

const App = () => (
  <BrowserRouter>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <div className="flex flex-col min-h-screen">
            {/* MongoDB Test Link - For easy access during development */}
            <div className="fixed bottom-20 right-4 z-50">
              <Link 
                to="/mongodb-test" 
                className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-md shadow-md text-sm font-medium"
              >
                <Database className="h-4 w-4" />
                MongoDB Test
              </Link>
            </div>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/recipes" element={<SimplifiedRecipesPage />} />
              <Route path="/folders" element={<FoldersPage />} />
              <Route path="/favorites" element={<FavoritesPage />} />
              <Route path="/shopping-list" element={<ShoppingListPage />} />
              <Route path="/recipe/:id" element={<RecipeDetailPage />} />
              <Route path="/manual-recipe/:id" element={<ManualRecipeDetailPage />} />
              <Route path="/external-recipe/:id" element={<ExternalRecipeDetailPage />} />
              <Route path="/add-recipe" element={<AddRecipePage />} />
              <Route path="/edit-recipe/:id" element={<EditRecipePage />} />
              <Route path="/mongodb-test" element={<MongoDBTestPage />} />
              <Route path="/signin" element={<SignInPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/preferences" element={<UserPreferencesPage />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
            <Footer />
            <Toaster />
            <Sonner />
          </div>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </BrowserRouter>
);

export default App;
