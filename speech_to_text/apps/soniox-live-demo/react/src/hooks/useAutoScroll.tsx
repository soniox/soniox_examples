import { useEffect, useRef } from "react";

export default function useAutoScroll(items: readonly unknown[]) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (items.length) {
      ref.current?.scrollTo({
        top: ref.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [items]);

  return ref;
}
