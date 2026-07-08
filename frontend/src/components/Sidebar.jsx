import { LayoutDashboard, BookOpen, Users, MessageSquare, Settings, LogOut } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, enabled: false },
  { to: "/knowledge", label: "Knowledge", icon: BookOpen, enabled: true },
  { to: "/leads", label: "Leads", icon: Users, enabled: false },
  { to: "/conversations", label: "Conversations", icon: MessageSquare, enabled: false },
  { to: "/settings", label: "Settings", icon: Settings, enabled: false },
];

function NavItems({ orientation }) {
  const isRow = orientation === "row";
  return (
    <>
      {NAV_ITEMS.map(({ to, label, icon: Icon, enabled }) =>
        enabled ? (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg font-medium transition-colors duration-150 ${
                isRow ? "flex-col gap-1 px-3 py-1.5 text-[11px]" : "px-3 py-2 text-sm"
              } ${
                isActive
                  ? "bg-accent/15 text-accent"
                  : "text-shell-text-muted hover:bg-white/5 hover:text-shell-text"
              }`
            }
          >
            <Icon className={isRow ? "h-5 w-5" : "h-[18px] w-[18px]"} strokeWidth={2} />
            {label}
          </NavLink>
        ) : (
          <span
            key={to}
            title="Coming soon"
            className={`flex cursor-not-allowed items-center gap-3 rounded-lg font-medium text-shell-text-muted/40 ${
              isRow ? "flex-col gap-1 px-3 py-1.5 text-[11px]" : "px-3 py-2 text-sm"
            }`}
          >
            <Icon className={isRow ? "h-5 w-5" : "h-[18px] w-[18px]"} strokeWidth={2} />
            {label}
          </span>
        )
      )}
    </>
  );
}

export default function Sidebar() {
  const { businessName, logout } = useAuth();

  return (
    <>
      {/* Desktop rail */}
      <aside className="hidden w-60 shrink-0 flex-col bg-base sm:flex">
        <div className="flex h-16 items-center gap-2 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent font-heading text-sm font-extrabold text-white">
            K
          </div>
          <span className="truncate font-heading text-sm font-bold text-shell-text">
            {businessName || "Khmer Assistant"}
          </span>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-2">
          <NavItems orientation="col" />
        </nav>
        <div className="border-t border-shell-border p-3">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-shell-text-muted transition-colors duration-150 hover:bg-white/5 hover:text-shell-text"
          >
            <LogOut className="h-[18px] w-[18px]" strokeWidth={2} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Mobile bottom bar */}
      <nav className="fixed inset-x-0 bottom-0 z-50 flex items-stretch justify-around border-t border-shell-border bg-base pb-[env(safe-area-inset-bottom)] sm:hidden">
        <NavItems orientation="row" />
      </nav>
    </>
  );
}
