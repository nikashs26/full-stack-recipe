
import { createClient } from '@supabase/supabase-js'

// Default values for local development if environment variables are not set
// Replace these with your actual Supabase project credentials
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://your-supabase-project-id.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'your-anon-key';

// Log connection status for debugging
console.log('Connecting to Supabase with URL:', supabaseUrl);
console.log('Supabase key available:', supabaseAnonKey ? 'Yes (key hidden)' : 'No');

// Validate that we have the required values
if (!supabaseUrl.includes('supabase.co') || supabaseAnonKey === 'your-anon-key') {
  console.error('Missing or invalid Supabase credentials. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
