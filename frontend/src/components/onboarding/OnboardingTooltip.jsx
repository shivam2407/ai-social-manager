import { useEffect, useState } from "react";
import { X } from "lucide-react";
import useSpotlight from "./useSpotlight";

const OFFSET = 14;
const TOOLTIP_W = 288; // w-72 = 18rem = 288px
const MARGIN = 12;

function getTooltipStyle(rect, position) {
  if (!rect) return { opacity: 0 };

  const vw = window.innerWidth;
  const isMobile = vw < 640;
  const tooltipW = isMobile ? vw - MARGIN * 2 : TOOLTIP_W;

  // On mobile, "right" position falls back to "bottom" since sidebar is a drawer
  const effectivePosition = isMobile && position === "right" ? "bottom" : position;

  switch (effectivePosition) {
    case "right": {
      let left = rect.left + rect.width + OFFSET;
      // If tooltip would overflow right edge, flip to bottom
      if (left + tooltipW > vw - MARGIN) {
        return {
          top: rect.top + rect.height + OFFSET,
          left: Math.max(MARGIN, Math.min(rect.left, vw - tooltipW - MARGIN)),
        };
      }
      return {
        top: rect.top + rect.height / 2,
        left,
        transform: "translateY(-50%)",
      };
    }
    case "bottom": {
      let left = rect.left + rect.width / 2 - tooltipW / 2;
      left = Math.max(MARGIN, Math.min(left, vw - tooltipW - MARGIN));
      return {
        top: rect.top + rect.height + OFFSET,
        left,
      };
    }
    case "left": {
      return {
        top: rect.top + rect.height / 2,
        right: vw - rect.left + OFFSET,
        transform: "translateY(-50%)",
      };
    }
    case "top": {
      let left = rect.left + rect.width / 2 - tooltipW / 2;
      left = Math.max(MARGIN, Math.min(left, vw - tooltipW - MARGIN));
      return {
        bottom: window.innerHeight - rect.top + OFFSET,
        left,
      };
    }
    default:
      return {};
  }
}

function Arrow({ position }) {
  const base = "absolute w-0 h-0";
  const border = "border-solid border-transparent";

  switch (position) {
    case "right":
      return (
        <div
          className={`${base} ${border}`}
          style={{
            top: "50%",
            left: -8,
            marginTop: -8,
            borderWidth: 8,
            borderRightColor: "#111827",
          }}
        />
      );
    case "bottom":
      return (
        <div
          className={`${base} ${border}`}
          style={{
            top: -8,
            left: "50%",
            marginLeft: -8,
            borderWidth: 8,
            borderBottomColor: "#111827",
          }}
        />
      );
    case "left":
      return (
        <div
          className={`${base} ${border}`}
          style={{
            top: "50%",
            right: -8,
            marginTop: -8,
            borderWidth: 8,
            borderLeftColor: "#111827",
          }}
        />
      );
    case "top":
      return (
        <div
          className={`${base} ${border}`}
          style={{
            bottom: -8,
            left: "50%",
            marginLeft: -8,
            borderWidth: 8,
            borderTopColor: "#111827",
          }}
        />
      );
    default:
      return null;
  }
}

export default function OnboardingTooltip({ step, onAction, onClose }) {
  const rect = useSpotlight(step.selector);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (rect) {
      requestAnimationFrame(() => setVisible(true));
    }
    return () => setVisible(false);
  }, [rect, step.id]);

  // Escape key to close
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!rect) return null;

  const isMobile = window.innerWidth < 640;
  const effectivePosition = isMobile && step.position === "right" ? "bottom" : step.position;

  const style = {
    ...getTooltipStyle(rect, step.position),
    opacity: visible ? 1 : 0,
    transition: "opacity 250ms ease-out, transform 250ms ease-out",
  };

  return (
    <div
      className="fixed z-[1002] w-72 max-sm:w-[calc(100vw-2rem)] bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-5"
      style={style}
    >
      <Arrow position={effectivePosition} />

      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-gray-600 hover:text-gray-400 transition-colors"
      >
        <X className="w-3.5 h-3.5" />
      </button>

      {/* Step badge */}
      {step.stepLabel && (
        <span className="inline-block bg-violet-500/20 text-violet-400 text-[10px] font-semibold uppercase rounded-full px-2 py-0.5 mb-2">
          {step.stepLabel}
        </span>
      )}

      {/* Title */}
      <h3 className="text-sm font-semibold text-white mb-1.5">{step.title}</h3>

      {/* Body */}
      <p className="text-xs text-gray-400 leading-relaxed mb-1">{step.body}</p>

      {/* Subtitle / hint */}
      {step.subtitle && (
        <p className="text-[11px] text-gray-500 italic mb-3">{step.subtitle}</p>
      )}

      {/* CTA button */}
      {step.cta && (
        <button
          onClick={() => {
            // For navigation steps, clicking the target element handles it
            const target = document.querySelector(step.selector);
            if (target) target.click();
            if (onAction) onAction();
          }}
          className="mt-3 w-full py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium transition-colors"
        >
          {step.cta}
        </button>
      )}
    </div>
  );
}
