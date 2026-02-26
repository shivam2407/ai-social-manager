import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import App from "./App";
import "./index.css";

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

function Root() {
  const inner = (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );

  // Only wrap with GoogleOAuthProvider when a client ID is configured
  if (googleClientId) {
    return <GoogleOAuthProvider clientId={googleClientId}>{inner}</GoogleOAuthProvider>;
  }
  return inner;
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
