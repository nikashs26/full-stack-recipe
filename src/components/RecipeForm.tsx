// AuthForm.jsx
import { useState } from 'react';
import { supabase } from '../supabaseClient.js'; // make sure this path is correct

export default function AuthForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      setMessage(error.message);
      setLoading(false);
      return;
    }

    const userId = data?.user?.id;

    if (userId) {
      const { error: insertError } = await supabase
        .from('users') // replace with your actual table name
        .insert([{ id: userId, email }]);

      if (insertError) {
        setMessage('Signed up, but error storing user data: ' + insertError.message);
      } else {
        setMessage('Signed up successfully!');
      }
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Signing up...' : 'Sign Up'}
      </button>
      {message && <p>{message}</p>}
    </form>
  );
}
