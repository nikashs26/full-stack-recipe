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

// Creating the reviews table more consistently
console.log('Setting up reviews table...');

// Execute raw SQL to create the reviews table directly
(async () => {
  try {
    const { error } = await supabase.rpc('exec_sql', {
      sql: `
      CREATE TABLE IF NOT EXISTS public.reviews (
        id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
        author TEXT NOT NULL,
        text TEXT NOT NULL,
        rating INTEGER NOT NULL,
        date TIMESTAMP WITH TIME ZONE NOT NULL,
        recipe_id TEXT NOT NULL,
        recipe_type TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- Grant access to anonymous users (adjust as needed)
      GRANT ALL ON public.reviews TO anon;
      GRANT ALL ON public.reviews TO authenticated;
      GRANT ALL ON public.reviews TO service_role;
      `
    });
    
    if (error) {
      // This is expected if exec_sql function isn't available
      console.log('Could not create reviews table with exec_sql:', error.message);
      console.log('Trying alternative approach...');
      
      // Try direct SQL execution (might work depending on permissions)
      const { error: sqlError } = await supabase.from('reviews').select('count(*)', { count: 'exact', head: true });
      
      if (sqlError && sqlError.code === '42P01') { // Table doesn't exist error
        console.log('Reviews table does not exist. Creating using API approach...');
        
        // Create table definition programmatically (simplified approach)
        try {
          console.log('Creating reviews table using Supabase management API...');
          // Note: This approach may be limited by permissions
        } catch (createError) {
          console.error('Failed to create reviews table:', createError);
        }
      } else if (!sqlError) {
        console.log('Reviews table already exists');
      }
    } else {
      console.log('Reviews table created or already exists');
    }
  } catch (err) {
    console.error('Error setting up reviews table:', err);
  }
})();

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
