// Debug script to test frontend API calls
console.log('🔍 Debugging Frontend API Call...');

// Test the exact same API call the frontend makes
const testRecommendationsAPI = async () => {
  try {
    console.log('📡 Making API call to /api/recommendations...');
    
    const response = await fetch('http://localhost:5004/api/recommendations?limit=5', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    console.log('📊 Response status:', response.status);
    console.log('📋 Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Success! Response data:', data);
      console.log('🍔 Found', data.recommendations?.length || 0, 'recommendations');
      
      if (data.recommendations?.length > 0) {
        console.log('📝 First recommendation:', data.recommendations[0]);
      }
    } else {
      const errorText = await response.text();
      console.log('❌ Error response:', errorText);
    }
  } catch (error) {
    console.log('💥 Network error:', error);
  }
};

// Test the frontend's exact API call
const testFrontendAPI = async () => {
  try {
    console.log('📡 Testing frontend-style API call...');
    
    // Simulate the frontend's apiCall function
    const API_BASE_URL = 'http://localhost:5004/api';
    const token = localStorage.getItem('auth_token');
    
    console.log('🔑 Token present:', !!token);
    
    const response = await fetch(`${API_BASE_URL}/recommendations?limit=5`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      credentials: 'include',
    });
    
    console.log('📊 Frontend response status:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Frontend success! Data:', data);
    } else {
      const errorText = await response.text();
      console.log('❌ Frontend error:', errorText);
    }
  } catch (error) {
    console.log('💥 Frontend network error:', error);
  }
};

// Run both tests
console.log('🧪 Running API tests...');
testRecommendationsAPI().then(() => {
  console.log('---');
  return testFrontendAPI();
}).then(() => {
  console.log('✅ Tests complete!');
}); 