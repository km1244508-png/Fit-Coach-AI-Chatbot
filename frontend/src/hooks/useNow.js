import { useEffect, useState } from "react";

// Re-renders every `ms` so "Today"/"Yesterday" groups stay correct across midnight.
export function useNow(ms = 60000) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), ms);
    return () => clearInterval(id);
  }, [ms]);
  return now;
}
