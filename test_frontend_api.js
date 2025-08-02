// Simple test to check frontend API call
const testFrontendAPI = async () => {
  console.log('🧪 Testing Frontend API Call...');
  
  // Simulate the frontend API call
  const API_BASE_URL = 'http://localhost:5004/api';
  const token = localStorage.getItem('auth_token');
  
  console.log('Token:', token ? 'Present' : 'Missing');
  
  try {
    const response = await fetch(`${API_BASE_URL}/recommendations?limit=5`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      credentials: 'include',
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Success! Found', data.recommendations?.length || 0, 'recommendations');
      console.log('First recommendation:', data.recommendations?.[0]?.name);
    } else {
      const errorData = await response.text();
      console.log('❌ Error:', errorData);
    }
  } catch (error) {
    console.log('❌ Network error:', error);
  }
};

// Run the test
testFrontendAPI(); 