
// This file is maintained for backward compatibility
// Please import from '@/integrations/supabase/client' instead

<<<<<<< HEAD
import { supabase, testSupabaseConnection } from '../integrations/supabase/client';
=======
// Check if we have actual environment variables or if we need to use fallbacks
// In a production environment, these should be properly set as environment variables
const supabaseUrl = 'https://zxbafomlbgoskgbsfsno.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4YmFmb21sYmdvc2tnYnNmc25vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2NDE4ODMsImV4cCI6MjA2MjIxNzg4M30.nWV8UMulWqzpEoDCpzPpQ8IQ1i_1QtBZ94TWTYO3xmw';
>>>>>>> a0fa3e0 (test agent)

export { supabase, testSupabaseConnection };
