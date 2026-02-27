import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import OnboardingProvider from "./onboarding/OnboardingProvider";

export default function Layout() {
  return (
    <OnboardingProvider>
      <div className="flex min-h-screen bg-gray-950">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-6 py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </OnboardingProvider>
  );
}
