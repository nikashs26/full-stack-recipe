import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import NotFound from "./pages/NotFound";
import Footer from "./components/Footer";
import HomePage from "./pages/HomePage";
import { Link } from "react-router-dom";
import { Utensils, Search } from "lucide-react";
import { AuthProvider } from "./context/AuthContext";

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
                to="/search" 
                className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-md shadow-md text-sm font-medium"
              >
                <Search className="h-4 w-4" />
                Search
              </Link>
            </div>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/search" element={<SearchPage />} />
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