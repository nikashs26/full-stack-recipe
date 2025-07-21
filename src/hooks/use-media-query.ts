import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const media = window.matchMedia(query);
    // Update the state with the current value
    setMatches(media.matches);
    
    // Create an event listener
    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    
    // Add the listener
    media.addEventListener('change', listener);
    
    // Remove the listener on cleanup
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}
