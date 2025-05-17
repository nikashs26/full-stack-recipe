
import { createClient } from '@supabase/supabase-js';

// Check if we have actual environment variables or if we need to use fallbacks
const supabaseUrl = 'https://zxbafomlbgoskgbsfsno.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4YmFmb21sYmdvc2tnYnNmc25vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2NDE4ODMsImV4cCI6MjA2MjIxNzg4M30.nWV8UMulWqzpEoDCpzPpQ8IQ1i_1QtBZ94TWTYO3xmw';

// Validate that we have the required values
if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase credentials. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables.');
}

// Create a single instance of the Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});

// Add a function to test the Supabase connection
export const testSupabaseConnection = async () => {
  try {
    console.log('Testing Supabase connection...');
    
    // Test the auth API
    console.log('Testing Supabase auth API...');
    const { error: authError } = await supabase.auth.getSession();
    
    if (authError) {
      console.error('Supabase auth API test failed:', authError);
      return { success: false, error: authError.message };
    }
    
    console.log('Supabase auth API test successful');
    
    // Attempt to query the sign-ups table
    try {
      console.log('Testing Supabase database API...');
      const { error } = await supabase.from('sign-ups').select('count()', { count: 'exact', head: true });
      
      if (error) {
        console.error('Supabase database API test failed:', error);
        console.warn(`The "sign-ups" table does not exist in your Supabase database or cannot be accessed.`);
        return { success: false, error: error.message, context: 'database' };
      }
      
      console.log('Supabase database connection successful');
      return { success: true };
    } catch (dbError) {
      console.error('Error testing database:', dbError);
      return { success: false, error: dbError instanceof Error ? dbError.message : 'Database error', context: 'database' };
    }
  } catch (error) {
    console.error('Error testing Supabase connection:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error connecting to Supabase'
    };
  }
};
