import { useContext } from "react";
import { OnboardingContext } from "./OnboardingProvider";

const NOOP = () => {};

const FALLBACK = {
  state: "IDLE",
  stepIndex: 0,
  currentStep: null,
  isActive: false,
  advance: NOOP,
  dismiss: NOOP,
  pause: NOOP,
  resume: NOOP,
  complete: NOOP,
  signal: NOOP,
  enterWaiting: NOOP,
  replay: NOOP,
  beginTutorial: NOOP,
};

export default function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  return ctx || FALLBACK;
}
