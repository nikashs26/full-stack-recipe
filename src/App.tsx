
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui/toaster';
import Index from './pages/Index';
import RecipesPage from './pages/RecipesPage';
import RecipeDetailPage from './pages/RecipeDetailPage';
import ExternalRecipeDetailPage from './pages/ExternalRecipeDetailPage';
import AddRecipePage from './pages/AddRecipePage';
import EditRecipePage from './pages/EditRecipePage';
import NotFound from './pages/NotFound';
import MongoDBTestPage from './pages/MongoDBTestPage';

const App: React.FC = () => {
  return (
    <>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/recipes" element={<RecipesPage />} />
        <Route path="/recipes/:id" element={<RecipeDetailPage />} />
        <Route path="/external-recipes/:id" element={<ExternalRecipeDetailPage />} />
        <Route path="/add-recipe" element={<AddRecipePage />} />
        <Route path="/edit-recipe/:id" element={<EditRecipePage />} />
        <Route path="/mongodb-test" element={<MongoDBTestPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Toaster />
    </>
  );
};

export default App;
