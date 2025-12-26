import { useEffect, useRef, useState } from "react";

export default function useJustAdded<T extends { id: number }>(items: T[]) {
  const prevIdsRef = useRef<Set<number> | null>(null);
  const [added, setAdded] = useState<Set<number>>(new Set());

  useEffect(() => {
    const currIds = new Set(items.map(i => i.id));
    const prevIds = prevIdsRef.current;

    if (prevIds === null) {
      prevIdsRef.current = currIds;
      return;
    }

    const newOnes = [...currIds].filter(id => !prevIds.has(id));
    if (newOnes.length > 0) {
      setAdded(prev => new Set([...prev, ...newOnes]));
    }

    prevIdsRef.current = currIds;
  }, [items]);

  return added;
}