import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { Loader2 } from "lucide-react";
import { googleAuthApi, githubAuthApi } from "../api";
import { useAuth } from "../context/AuthContext";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;

export default function OAuthButtons({ onError }) {
  const [loading, setLoading] = useState(null); // "google" | "github" | null
  const { login } = useAuth();
  const navigate = useNavigate();

  // Don't render anything if neither provider is configured
  if (!GOOGLE_CLIENT_ID && !GITHUB_CLIENT_ID) return null;

  const handleOAuthSuccess = (data) => {
    login(data.access_token, data.user);
    navigate("/");
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setLoading("google");
    try {
      const data = await googleAuthApi(credentialResponse.credential);
      handleOAuthSuccess(data);
    } catch (err) {
      onError?.(err.message);
    } finally {
      setLoading(null);
    }
  };

  const handleGitHubClick = () => {
    if (!GITHUB_CLIENT_ID) {
      onError?.("GitHub OAuth not configured");
      return;
    }
    const redirectUri = `${window.location.origin}/login`;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user:email`;
  };

  return (
    <div className="space-y-3">
      {GOOGLE_CLIENT_ID && (
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => onError?.("Google sign-in failed")}
            theme="filled_black"
            size="large"
            width="100%"
            text="continue_with"
          />
        </div>
      )}

      {GITHUB_CLIENT_ID && (
        <button
          type="button"
          onClick={handleGitHubClick}
          disabled={loading === "github"}
          className="w-full py-2.5 rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading === "github" ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          )}
          Continue with GitHub
        </button>
      )}

      <div className="flex items-center gap-3 my-1">
        <div className="flex-1 h-px bg-gray-800" />
        <span className="text-xs text-gray-500">or</span>
        <div className="flex-1 h-px bg-gray-800" />
      </div>
    </div>
  );
}
