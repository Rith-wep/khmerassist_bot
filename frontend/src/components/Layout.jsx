import { LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  const { isAuthenticated, businessName, logout } = useAuth();

  if (!isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen bg-page">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile top bar (sidebar header is desktop-only) */}
        <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 sm:hidden">
          <span className="truncate font-heading text-sm font-bold text-ink">
            {businessName || "Dashboard"}
          </span>
          <button
            onClick={logout}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors duration-150 hover:bg-gray-100"
            aria-label="Sign out"
          >
            <LogOut className="h-[18px] w-[18px]" strokeWidth={2} />
          </button>
        </header>

        <main className="flex-1 px-4 py-6 pb-20 sm:px-8 sm:py-8 sm:pb-8">{children}</main>
      </div>
    </div>
  );
}
