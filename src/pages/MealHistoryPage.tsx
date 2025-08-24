import React from 'react';
import { Clock, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import MealPlanHistory from '../components/MealPlanHistory';

const MealHistoryPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link 
            to="/" 
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center space-x-3">
            <div className="h-12 w-12 rounded-full bg-recipe-primary/20 flex items-center justify-center">
              <Clock className="h-6 w-6 text-recipe-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Meal History</h1>
              <p className="text-gray-600">Track your cooking journey and meal planning history</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <MealPlanHistory />
        </div>
      </div>
    </div>
  );
};

export default MealHistoryPage;
