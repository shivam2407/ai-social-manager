import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Sparkles,
  History,
  Settings,
  Zap,
} from "lucide-react";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/generate", icon: Sparkles, label: "Generate" },
  { to: "/history", icon: History, label: "History" },
  { to: "/brand", icon: Settings, label: "Brand Settings" },
];

export default function Sidebar() {
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
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
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
      <div className="px-5 py-4 border-t border-gray-800 text-xs text-gray-600">
        Multi-Agent Pipeline
      </div>
    </aside>
  );
}
