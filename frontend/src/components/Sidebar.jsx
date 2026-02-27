import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Sparkles,
  History,
  Settings,
  Key,
  Zap,
  LogOut,
  RotateCcw,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import useOnboarding from "./onboarding/useOnboarding";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", onboarding: null },
  { to: "/generate", icon: Sparkles, label: "Generate", onboarding: "generate-link" },
  { to: "/history", icon: History, label: "History", onboarding: null },
  { to: "/brand", icon: Settings, label: "Brand Settings", onboarding: "brand-settings-link" },
  { to: "/settings", icon: Key, label: "API Keys", onboarding: "api-keys-link" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { state: onboardingState, replay } = useOnboarding();
  const showReplay = onboardingState === "IDLE" && user?.onboarding_completed;

  return (
    <aside className="w-64 shrink-0 border-r border-gray-800 bg-gray-950 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-800">
        <Zap className="w-6 h-6 text-violet-400" />
        <span className="text-lg font-bold tracking-tight text-white">
          AI Social Manager
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, icon: Icon, label, onboarding }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            data-onboarding={onboarding || undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-violet-500/15 text-violet-400"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
              }`
            }
          >
            <Icon className="w-4.5 h-4.5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-800 space-y-3">
        {showReplay && (
          <button
            onClick={replay}
            className="flex items-center gap-2 text-xs text-gray-600 hover:text-violet-400 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Replay Tutorial
          </button>
        )}
        {user && (
          <p className="text-xs text-gray-500 truncate">{user.email}</p>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Logout
        </button>
      </div>
    </aside>
  );
}
