import { useState, useEffect, useCallback } from "react";

export default function useSpotlight(selector) {
  const [rect, setRect] = useState(null);

  const update = useCallback(() => {
    if (!selector) {
      setRect(null);
      return;
    }
    const el = document.querySelector(selector);
    if (el) {
      const r = el.getBoundingClientRect();
      setRect({ top: r.top, left: r.left, width: r.width, height: r.height });
    } else {
      setRect(null);
    }
  }, [selector]);

  useEffect(() => {
    update();

    const observer = new ResizeObserver(update);
    observer.observe(document.body);

    window.addEventListener("scroll", update, true);
    window.addEventListener("resize", update);

    // Poll briefly for elements that may not be rendered yet
    const interval = setInterval(update, 500);
    const timeout = setTimeout(() => clearInterval(interval), 5000);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("resize", update);
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [update]);

  return rect;
}
