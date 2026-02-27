import { createContext, useReducer, useEffect, useCallback, useRef } from "react";
import { useLocation } from "react-router-dom";
import { STEPS } from "./onboardingSteps";
import { getBrands, getApiKeys, getHistoryApi, updateOnboardingStatus } from "../../api";
import { useAuth } from "../../context/AuthContext";
import OnboardingOverlay from "./OnboardingOverlay";
import WelcomeModal from "./WelcomeModal";
import OnboardingTooltip from "./OnboardingTooltip";
import CompletionToast from "./CompletionToast";
import ResumePill from "./ResumePill";

export const OnboardingContext = createContext(null);

const initialState = {
  status: "IDLE", // IDLE | WELCOME | ACTIVE | WAITING | PAUSED | CELEBRATING
  stepIndex: 0,
  initialized: false,
};

function reducer(state, action) {
  switch (action.type) {
    case "START":
      return { ...state, status: "WELCOME", stepIndex: 0, initialized: true };
    case "START_AT":
      return { ...state, status: "ACTIVE", stepIndex: action.stepIndex, initialized: true };
    case "ADVANCE":
      return { ...state, status: "ACTIVE", stepIndex: state.stepIndex + 1 };
    case "SET_STEP":
      return { ...state, status: "ACTIVE", stepIndex: action.stepIndex };
    case "WAITING":
      return { ...state, status: "WAITING" };
    case "PAUSE":
      return { ...state, status: "PAUSED" };
    case "RESUME":
      return { ...state, status: "ACTIVE" };
    case "CELEBRATE":
      return { ...state, status: "CELEBRATING" };
    case "COMPLETE":
      return { ...state, status: "IDLE", initialized: true };
    case "IDLE":
      return { ...state, status: "IDLE", initialized: true };
    default:
      return state;
  }
}

export default function OnboardingProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const location = useLocation();
  const checkRef = useRef(false);
  const stepIndexRef = useRef(state.stepIndex);
  stepIndexRef.current = state.stepIndex;
  const { user, setUser } = useAuth();

  // Persist onboarding_completed to DB and update user in-memory
  const setOnboardingCompleted = useCallback(
    (completed) => {
      updateOnboardingStatus(completed).catch(() => {});
      if (user) {
        setUser({ ...user, onboarding_completed: completed });
      }
    },
    [user, setUser],
  );

  // Check milestones and decide whether to start
  useEffect(() => {
    if (checkRef.current) return;
    checkRef.current = true;

    if (user?.onboarding_completed) {
      dispatch({ type: "IDLE" });
      return;
    }

    // Check current user state
    Promise.all([
      getBrands().catch(() => []),
      getApiKeys().catch(() => []),
      getHistoryApi(1).catch(() => []),
    ]).then(([brands, keys, history]) => {
      const hasBrands = brands.length > 0;
      const hasDefaultKey = keys.some((k) => k.is_default);
      const hasGenerations = history.length > 0;

      if (hasGenerations) {
        setOnboardingCompleted(true);
        dispatch({ type: "IDLE" });
        return;
      }

      // Adaptive start: skip completed milestones
      if (hasBrands && hasDefaultKey) {
        dispatch({ type: "START_AT", stepIndex: 5 });
      } else if (hasBrands) {
        dispatch({ type: "START_AT", stepIndex: 3 });
      } else {
        dispatch({ type: "START" });
      }
    });
  }, []);

  // Watch for page navigation to advance navigation-based steps
  useEffect(() => {
    if (state.status !== "ACTIVE" && state.status !== "WAITING") return;

    const step = STEPS[state.stepIndex];
    if (!step) return;

    // If step has advanceTo and user is already on that page, advance
    if (step.advanceTo && location.pathname === step.advanceTo) {
      dispatch({ type: "ADVANCE" });
      return;
    }

    // If step requires a specific page and user is on a different page,
    // skip ahead to a step that matches (or has no page constraint)
    if (step.page && step.page !== location.pathname && step.type === "tooltip") {
      const nextMatchingStep = STEPS.findIndex(
        (s, i) => i > state.stepIndex && (!s.page || s.page === location.pathname)
      );
      if (nextMatchingStep !== -1) {
        dispatch({ type: "SET_STEP", stepIndex: nextMatchingStep });
      }
    }
  }, [location.pathname, state.status, state.stepIndex]);

  const advance = useCallback(() => {
    const nextIndex = state.stepIndex + 1;
    if (nextIndex >= STEPS.length) {
      dispatch({ type: "CELEBRATE" });
    } else {
      dispatch({ type: "ADVANCE" });
    }
  }, [state.stepIndex]);

  const dismiss = useCallback(() => {
    setOnboardingCompleted(true);
    dispatch({ type: "COMPLETE" });
  }, [setOnboardingCompleted]);

  const pause = useCallback(() => {
    dispatch({ type: "PAUSE" });
  }, []);

  const resume = useCallback(() => {
    // Re-evaluate milestones
    Promise.all([
      getBrands().catch(() => []),
      getApiKeys().catch(() => []),
    ]).then(([brands, keys]) => {
      const hasBrands = brands.length > 0;
      const hasDefaultKey = keys.some((k) => k.is_default);

      let targetStep = state.stepIndex;
      if (hasBrands && hasDefaultKey && targetStep < 5) {
        targetStep = 5;
      } else if (hasBrands && targetStep < 3) {
        targetStep = 3;
      }
      dispatch({ type: "SET_STEP", stepIndex: targetStep });
    });
  }, [state.stepIndex]);

  const complete = useCallback(() => {
    setOnboardingCompleted(true);
    dispatch({ type: "COMPLETE" });
  }, [setOnboardingCompleted]);

  const signal = useCallback((event) => {
    const step = STEPS[stepIndexRef.current];
    if (!step) return;

    if (event === "brand-created" && step.advanceOn === "brand-created") {
      advance();
    } else if (event === "default-key-set" && step.advanceOn === "default-key-set") {
      advance();
    } else if (event === "generation-complete") {
      dispatch({ type: "CELEBRATE" });
    }
  }, [advance]);

  // Enter waiting state when user starts filling form
  const enterWaiting = useCallback(() => {
    if (state.status === "ACTIVE") {
      dispatch({ type: "WAITING" });
    }
  }, [state.status]);

  const replay = useCallback(() => {
    setOnboardingCompleted(false);
    dispatch({ type: "START" });
  }, [setOnboardingCompleted]);

  const beginTutorial = useCallback(() => {
    dispatch({ type: "ADVANCE" });
  }, []);

  const currentStep = STEPS[state.stepIndex] || null;

  const ctxValue = {
    state: state.status,
    stepIndex: state.stepIndex,
    currentStep,
    isActive: state.status === "ACTIVE" || state.status === "WAITING" || state.status === "WELCOME",
    advance,
    dismiss,
    pause,
    resume,
    complete,
    signal,
    enterWaiting,
    replay,
    beginTutorial,
  };

  return (
    <OnboardingContext.Provider value={ctxValue}>
      {children}
      {state.status === "WELCOME" && (
        <WelcomeModal onStart={beginTutorial} onSkip={dismiss} />
      )}
      {state.status === "ACTIVE" && currentStep?.type === "tooltip" && (!currentStep.page || currentStep.page === location.pathname) && (
        <>
          <OnboardingOverlay
            selector={currentStep.selector}
            onClickOverlay={pause}
          />
          <OnboardingTooltip
            step={currentStep}
            onAction={() => {
              if (currentStep.cta && currentStep.advanceOn) {
                enterWaiting();
              }
            }}
            onClose={pause}
          />
        </>
      )}
      {state.status === "PAUSED" && <ResumePill onResume={resume} />}
      {state.status === "CELEBRATING" && (
        <CompletionToast onDone={complete} />
      )}
    </OnboardingContext.Provider>
  );
}
