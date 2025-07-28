
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
import MealDBRecipesPage from "./pages/MealDBRecipesPage";
import SearchPage from "./pages/SearchPage";

import NotFound from "./pages/NotFound";
import Footer from "./components/Footer";
import HomePage from "./pages/HomePage";
import FoldersPage from "./pages/FoldersPage";
import FavoritesPage from "./pages/FavoritesPage";
import ShoppingListPage from "./pages/ShoppingListPage";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import UserPreferencesPage from "./pages/UserPreferencesPage";
import { Link } from "react-router-dom";
import { Database, Utensils } from "lucide-react";
import { AuthProvider } from "./context/AuthContext";

import ManualRecipeDetailPage from "./pages/ManualRecipeDetailPage";

import { FolderDetail } from './components/folders/FolderDetail';
import MealPlannerPage from './pages/MealPlannerPage';


const queryClient = new QueryClient();

const App = () => (
  <BrowserRouter>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <div className="flex flex-col min-h-screen">
            {/* Development Tools - For easy access during development */}
            <div className="fixed bottom-20 right-4 z-50 flex flex-col gap-2">
              <Link 
                to="/mongodb-test" 
                className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-md shadow-md text-sm font-medium"
              >
                <Database className="h-4 w-4" />
                MongoDB Test
              </Link>
              <Link 
                to="/themealdb" 
                className="flex items-center gap-1 bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-md shadow-md text-sm font-medium"
              >
                <Utensils className="h-4 w-4" />
                TheMealDB
              </Link>
            </div>
            <Routes>
              <Route path="/" element={<HomePage />} />
              {/* <Route path="/recipes" element={<RecipesPage />} /> */}
              <Route path="/search" element={<SearchPage />} />
              <Route path="/themealdb" element={<MealDBRecipesPage />} />
              <Route path="/recipes/:id" element={<RecipeDetailPage />} />
              <Route path="/external-recipe/:id" element={<ExternalRecipeDetailPage />} />
              <Route path="/manual-recipe/:id" element={<ManualRecipeDetailPage />} />
              <Route path="/add-recipe" element={<AddRecipePage />} />
              <Route path="/edit-recipe/:id" element={<EditRecipePage />} />
              <Route path="/folders" element={<FoldersPage />} />
              {/* <Route path="/folders/:folderId" element={<FolderDetail />} /> */}
              <Route path="/favorites" element={<FavoritesPage />} />
              {/* <Route path="/shopping-list" element={<ShoppingListPage />} /> */}
              <Route path="/signin" element={<SignInPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/preferences" element={<UserPreferencesPage />} />
              <Route path="/meal-planner" element={<MealPlannerPage />} />

              <Route path="*" element={<NotFound />} />
            </Routes>
            <Footer />
          </div>
          <Toaster />
          <Sonner />
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </BrowserRouter>
);

export default App;
