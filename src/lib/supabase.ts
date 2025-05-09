
import { createClient } from '@supabase/supabase-js'

// These values should be stored in environment variables
// For now, we'll use placeholders that you'll need to replace with your actual Supabase credentials
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://zxbafomlbgoskgbsfsno.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4YmFmb21sYmdvc2tnYnNmc25vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2NDE4ODMsImV4cCI6MjA2MjIxNzg4M30.nWV8UMulWqzpEoDCpzPpQ8IQ1i_1QtBZ94TWTYO3xmw';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
