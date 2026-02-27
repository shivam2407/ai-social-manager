import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, Zap } from "lucide-react";
import Sidebar from "./Sidebar";
import OnboardingProvider from "./onboarding/OnboardingProvider";

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Close sidebar drawer on any route change (covers onboarding CTA clicks too)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <OnboardingProvider>
      <div className="flex min-h-screen bg-gray-950">
        {/* Mobile header */}
        <div className="fixed top-0 left-0 right-0 z-40 flex items-center gap-3 px-4 py-3 bg-gray-950 border-b border-gray-800 md:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          <Zap className="w-5 h-5 text-violet-400" />
          <span className="text-sm font-bold text-white">AI Social Manager</span>
        </div>

        {/* Mobile backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/60 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div
          className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-200 ease-in-out md:static md:translate-x-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <Sidebar onClose={() => setSidebarOpen(false)} />
        </div>

        <main className="flex-1 overflow-y-auto pt-14 md:pt-0">
          <div className="max-w-5xl mx-auto px-4 py-6 md:px-6 md:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </OnboardingProvider>
  );
}
