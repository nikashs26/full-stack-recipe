
import { createClient } from '@supabase/supabase-js';

// These values should be stored in environment variables
// For now, we'll use placeholders that you'll need to replace with your actual Supabase credentials
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'YOUR_SUPABASE_URL';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
