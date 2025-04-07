
import React from 'react';
import Header from '../components/Header';
import MongoDBTester from '../components/MongoDBTester';

const MongoDBTestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">MongoDB Testing Tool</h1>
        <p className="mb-6 text-gray-600">
          Use this tool to test your MongoDB connection and add sample recipes directly to your database.
        </p>
        <MongoDBTester />
      </main>
    </div>
  );
};

export default MongoDBTestPage;
