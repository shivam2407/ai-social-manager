import { useEffect, useState } from "react";
import useSpotlight from "./useSpotlight";

const PAD = 6;
const ROUND = 8;

export default function OnboardingOverlay({ selector, onClickOverlay }) {
  const rect = useSpotlight(selector);
  const [clipPath, setClipPath] = useState("none");

  useEffect(() => {
    if (rect) {
      const top = rect.top - PAD;
      const left = rect.left - PAD;
      const right = rect.left + rect.width + PAD;
      const bottom = rect.top + rect.height + PAD;

      // Single continuous polygon that traces the viewport perimeter then dips
      // inward to carve a rectangular hole for the spotlight target.
      //
      //  (0,0)───────────────────────────(100%,0)
      //   │                                    │
      //   │    (left,top)───────(right,top)     │
      //   │    │    spotlight hole    │          │
      //   │    (left,btm)───────(right,btm)     │
      //   │                                     │
      //  (0,100%)────────────────────────(100%,100%)
      //
      setClipPath(
        `polygon(evenodd,
          0% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%,
          ${left}px ${top}px,
          ${left}px ${bottom}px,
          ${right}px ${bottom}px,
          ${right}px ${top}px,
          ${left}px ${top}px
        )`
      );
    } else {
      setClipPath("none");
    }
  }, [rect]);

  return (
    <>
      {/* Dark overlay with spotlight cutout */}
      <div
        className="fixed inset-0 z-[1000] bg-black/50 backdrop-blur-[2px]"
        style={{
          clipPath,
          WebkitClipPath: clipPath,
          transition: "clip-path 400ms cubic-bezier(0.4, 0, 0.2, 1)",
        }}
        onClick={onClickOverlay}
      />
      {/* Glow ring around spotlight target */}
      {rect && (
        <div
          className="fixed z-[1001] pointer-events-none onboarding-glow"
          style={{
            top: rect.top - PAD,
            left: rect.left - PAD,
            width: rect.width + PAD * 2,
            height: rect.height + PAD * 2,
            borderRadius: ROUND,
          }}
        />
      )}
    </>
  );
}
