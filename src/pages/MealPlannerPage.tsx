import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Recipe } from '../types/recipe'; // Assuming you have a Recipe type
import { useAuth } from '../context/AuthContext'; // To get user ID
import { Link } from 'react-router-dom';

interface MealPlan {
  [day: string]: {
    breakfast: Recipe | null;
    lunch: Recipe | null;
    dinner: Recipe | null;
  };
}

const daysOfWeek = [
  'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
];
const mealTypes = ['breakfast', 'lunch', 'dinner'];

const MealPlannerPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generatePlan = async () => {
    if (!isAuthenticated || !user?.id) {
      setError("Please log in to generate a meal plan.");
      return;
    }

    setLoading(true);
    setError(null);
    setMealPlan(null);

    try {
      const token = localStorage.getItem('token'); // Assuming token is stored here
      const response = await fetch('/api/meal-plan/generate', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate meal plan");
      }

      const data = await response.json();
      setMealPlan(data.plan);

    } catch (err: any) {
      console.error("Error generating meal plan:", err);
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">Weekly Meal Planner</h1>
            <p className="text-lg text-gray-600">
              Let our agent create a personalized meal plan for your week based on your preferences.
            </p>
            {!isAuthenticated && (
              <p className="text-red-500 mt-4">You must be logged in to use the meal planner.</p>
            )}
          </div>

          <div className="flex justify-center mb-8">
            <Button 
              onClick={generatePlan}
              disabled={loading || !isAuthenticated}
              className="px-8 py-3 text-lg"
            >
              {loading ? "Generating Plan..." : "Generate My Weekly Plan"}
            </Button>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-8" role="alert">
              <strong className="font-bold">Error:</strong>
              <span className="block sm:inline"> {error}</span>
              {error.includes("No recipes match") && (
                <p className="mt-2 text-sm">Consider adjusting your <Link to="/preferences" className="text-red-800 underline">preferences</Link>.</p>
              )}
            </div>
          )}

          {mealPlan && (
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-2xl font-bold mb-6 text-center">Your Weekly Plan</h2>
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7">
                {daysOfWeek.map(day => (
                  <div key={day} className="border rounded-lg p-4 bg-gray-50 shadow-sm">
                    <h3 className="text-xl font-semibold mb-4 capitalize text-center text-blue-700">{day}</h3>
                    {mealTypes.map(mealType => (
                      <div key={mealType} className="mb-4 last:mb-0">
                        <p className="font-medium text-gray-700 mb-1 capitalize">{mealType}:</p>
                        <div className="bg-white border border-gray-200 rounded p-3 min-h-[80px] flex items-center justify-center text-center">
                          {mealPlan[day][mealType] && mealPlan[day][mealType]?.id !== "none" ? (
                            <span className="text-gray-800 font-semibold">
                              <Link to={`/recipes/${mealPlan[day][mealType]?.id}`} className="hover:underline text-blue-600">
                                {mealPlan[day][mealType]?.name}
                              </Link>
                            </span>
                          ) : (
                            <span className="text-gray-500 italic text-sm">No recipe assigned</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default MealPlannerPage; 