import { useEffect, useRef } from "react";

export default function useAutoScroll(messages: unknown[]) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messages.length) {
      ref.current?.scrollTo({
        top: ref.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  return ref;
}
