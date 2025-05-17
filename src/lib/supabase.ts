
import { createClient } from '@supabase/supabase-js';

// Check if we have actual environment variables or if we need to use fallbacks
// In a production environment, these should be properly set as environment variables
const supabaseUrl = 'https://zxbafomlbgoskgbsfsno.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4YmFmb21sYmdvc2tnYnNmc25vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2NDE4ODMsImV4cCI6MjA2MjIxNzg4M30.nWV8UMulWqzpEoDCpzPpQ8IQ1i_1QtBZ94TWTYO3xmw';

// Validate that we have the required values
if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase credentials. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Add a function to test the Supabase connection
export const testSupabaseConnection = async () => {
  try {
    console.log('Testing Supabase connection...');
    const { data, error } = await supabase.from('reviews').select('count()', { count: 'exact', head: true });
    
    if (error) {
      console.error('Supabase connection test failed:', error);
      
      // Check if it's a "relation does not exist" error (table doesn't exist)
      if (error.message.includes('does not exist')) {
        console.warn('The "reviews" table does not exist in your Supabase database');
        console.warn('Please create a table with the following structure:');
        console.warn(`
          Table name: reviews
          Columns:
          - id: uuid (primary key, default: uuid_generate_v4())
          - author: text
          - text: text
          - rating: integer
          - date: timestamp with time zone
          - recipe_id: text
          - recipe_type: text
        `);
      }
      
      return { success: false, error: error.message };
    }
    
    console.log('Supabase connection successful:', data);
    return { success: true };
  } catch (error) {
    console.error('Error testing Supabase connection:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error connecting to Supabase'
    };
  }
};

// Run the connection test when this module is imported
testSupabaseConnection();
