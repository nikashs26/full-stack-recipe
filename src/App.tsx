
import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from '@/components/ui/toaster';
import './App.css';

// Lazy load components
const Index = lazy(() => import('./pages/Index'));
const RecipesPage = lazy(() => import('./pages/RecipesPage'));
const AddRecipePage = lazy(() => import('./pages/AddRecipePage'));
const RecipeDetailPage = lazy(() => import('./pages/RecipeDetailPage'));
const ManualRecipeDetailPage = lazy(() => import('./pages/ManualRecipeDetailPage'));
const ExternalRecipeDetailPage = lazy(() => import('./pages/ExternalRecipeDetailPage'));
const EditRecipePage = lazy(() => import('./pages/EditRecipePage'));
const ShoppingListPage = lazy(() => import('./pages/ShoppingListPage'));
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'));
const FoldersPage = lazy(() => import('./pages/FoldersPage'));
const UserPreferencesPage = lazy(() => import('./pages/UserPreferencesPage'));
const SignInPage = lazy(() => import('./pages/SignInPage'));
const SignUpPage = lazy(() => import('./pages/SignUpPage'));
const MongoDBTestPage = lazy(() => import('./pages/MongoDBTestPage'));
const NotFound = lazy(() => import('./pages/NotFound'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60000, // 1 minute
      retry: 1
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="App">
          <Suspense fallback={<div className="flex justify-center items-center min-h-screen">Loading...</div>}>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/recipes" element={<RecipesPage />} />
              <Route path="/add-recipe" element={<AddRecipePage />} />
              <Route path="/recipe/:id" element={<RecipeDetailPage />} />
              <Route path="/manual-recipe/:id" element={<ManualRecipeDetailPage />} />
              <Route path="/external-recipe/:id" element={<ExternalRecipeDetailPage />} />
              <Route path="/edit-recipe/:id" element={<EditRecipePage />} />
              <Route path="/shopping-list" element={<ShoppingListPage />} />
              <Route path="/favorites" element={<FavoritesPage />} />
              <Route path="/folders" element={<FoldersPage />} />
              <Route path="/preferences" element={<UserPreferencesPage />} />
              <Route path="/signin" element={<SignInPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/mongodb-test" element={<MongoDBTestPage />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
          <Toaster />
        </div>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
