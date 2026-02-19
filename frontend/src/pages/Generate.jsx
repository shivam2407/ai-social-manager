import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { generateContent, getBrands, getApiKeys } from "../api";
import StepIndicator from "../components/StepIndicator";
import StepSelectBrand from "../components/StepSelectBrand";
import StepCompose from "../components/StepCompose";
import StepResults from "../components/StepResults";

const stageTimings = [
  { key: "research", delay: 0 },
  { key: "strategy", delay: 4000 },
  { key: "writing", delay: 8000 },
  { key: "review", delay: 12000 },
];

export default function Generate() {
  const [step, setStep] = useState(1);
  const [brands, setBrands] = useState([]);
  const [brandsLoading, setBrandsLoading] = useState(true);
  const [selectedBrandId, setSelectedBrandId] = useState(null);

  const [contentRequest, setContentRequest] = useState("");
  const [images, setImages] = useState([]);
  const [platforms, setPlatforms] = useState(["twitter", "linkedin"]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeStage, setActiveStage] = useState(null);
  const [completedStages, setCompletedStages] = useState([]);
  const [hasDefaultKey, setHasDefaultKey] = useState(true);

  const timersRef = useRef([]);

  const selectedBrand = brands.find((b) => b.id === selectedBrandId);

  // Fetch brands whenever step transitions to 1
  const fetchBrands = useCallback(() => {
    setBrandsLoading(true);
    getBrands()
      .then((data) => setBrands(data))
      .catch(() => setBrands([]))
      .finally(() => setBrandsLoading(false));
  }, []);

  useEffect(() => {
    if (step === 1) fetchBrands();
  }, [step, fetchBrands]);

  // Check for default API key on mount
  useEffect(() => {
    getApiKeys()
      .then((keys) => setHasDefaultKey(keys.some((k) => k.is_default)))
      .catch(() => setHasDefaultKey(false));
  }, []);

  const togglePlatform = (p) =>
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
    );

  const simulateStages = () => {
    setCompletedStages([]);
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];

    stageTimings.forEach(({ key, delay }, i) => {
      const t1 = setTimeout(() => setActiveStage(key), delay);
      timersRef.current.push(t1);
      if (i > 0) {
        const prevKey = stageTimings[i - 1].key;
        const t2 = setTimeout(
          () => setCompletedStages((prev) => [...prev, prevKey]),
          delay,
        );
        timersRef.current.push(t2);
      }
    });
  };

  const handleGenerate = async () => {
    if (!selectedBrand || !contentRequest || platforms.length === 0) {
      setError(
        "Please fill in a content request and select at least one platform.",
      );
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setStep(3);
    simulateStages();

    try {
      const data = await generateContent({
        brand_name: selectedBrand.brand_name,
        niche: selectedBrand.niche,
        target_audience: selectedBrand.target_audience || "general audience",
        voice_description: selectedBrand.voice_description,
        tone_keywords: selectedBrand.tone_keywords,
        example_posts: selectedBrand.example_posts,
        content_request: contentRequest,
        target_platforms: platforms,
        images,
      });

      setResult(data);
      setActiveStage(null);
      setCompletedStages(stageTimings.map((s) => s.key));
    } catch (err) {
      setError(err.message);
      setActiveStage(null);
      setCompletedStages([]);
      // Return to compose step on error
      setStep(2);
    } finally {
      setLoading(false);
      timersRef.current.forEach(clearTimeout);
    }
  };

  const handleStepClick = (targetStep) => {
    if (targetStep < step) setStep(targetStep);
  };

  const handleGenerateAgain = () => {
    setResult(null);
    setError(null);
    setActiveStage(null);
    setCompletedStages([]);
    setStep(2);
  };

  const handleDifferentBrand = () => {
    setResult(null);
    setError(null);
    setActiveStage(null);
    setCompletedStages([]);
    setContentRequest("");
    setImages([]);
    setStep(1);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Generate Content</h1>
        <p className="text-sm text-gray-500 mt-1">
          Select a brand, compose your request, and generate platform-specific
          posts.
        </p>
      </div>

      {!hasDefaultKey && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>
            No default API key configured.{" "}
            <Link to="/settings" className="underline hover:text-amber-300">
              Go to Settings
            </Link>{" "}
            to add one before generating content.
          </span>
        </div>
      )}

      <StepIndicator currentStep={step} onStepClick={handleStepClick} />

      {step === 1 && (
        <StepSelectBrand
          brands={brands}
          loading={brandsLoading}
          selectedBrandId={selectedBrandId}
          onSelect={setSelectedBrandId}
          onContinue={() => setStep(2)}
        />
      )}

      {step === 2 && selectedBrand && (
        <StepCompose
          brand={selectedBrand}
          contentRequest={contentRequest}
          setContentRequest={setContentRequest}
          images={images}
          setImages={setImages}
          platforms={platforms}
          togglePlatform={togglePlatform}
          onGenerate={handleGenerate}
          onChangeBrand={() => setStep(1)}
          loading={loading}
          error={error}
          hasDefaultKey={hasDefaultKey}
        />
      )}

      {step === 3 && (
        <StepResults
          result={result}
          loading={loading}
          activeStage={activeStage}
          completedStages={completedStages}
          onGenerateAgain={handleGenerateAgain}
          onDifferentBrand={handleDifferentBrand}
        />
      )}
    </div>
  );
}
