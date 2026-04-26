"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { logout } from "@/lib/api/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const settingsMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (
        settingsMenuRef.current &&
        !settingsMenuRef.current.contains(event.target as Node)
      ) {
        setIsSettingsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    setUser(null);
    router.push("/");
  };

  if (!user) {
    return <div className="page-shell flex items-center justify-center">Loading...</div>;
  }

  const navItems = [
    { name: "Resumes", path: "/dashboard/resumes" },
    { name: "Outreach", path: "/dashboard/outreach" },
    { name: "Answers", path: "/dashboard/answers" },
  ];

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Top Navigation Ribbon */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-8">
          <h1 className="font-display font-bold text-xl tracking-tight text-[var(--accent)]">Widenet</h1>
          
          <nav className="hidden md:flex gap-1">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.path);
              return (
                <Link 
                  key={item.path} 
                  href={item.path}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                    isActive 
                      ? "bg-[var(--accent-soft)] text-[var(--accent)]" 
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => router.push("/dashboard/profile")}
            className={`text-sm font-semibold hidden sm:inline-flex items-center gap-2 transition cursor-pointer ${
              pathname.startsWith("/dashboard/profile")
                ? "text-[var(--accent)]"
                : "text-slate-700 hover:text-[var(--accent)]"
            }`}
            aria-label="Open profile"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M20 21a8 8 0 0 0-16 0" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            {user.name}
          </button>
          <div className="relative" ref={settingsMenuRef}>
            <button
              type="button"
              aria-label="Open settings menu"
              aria-haspopup="menu"
              aria-expanded={isSettingsOpen}
              onClick={() => setIsSettingsOpen((prev) => !prev)}
              className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-slate-600 hover:text-[var(--accent)] hover:bg-slate-100 transition"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 15.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7z" />
                <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 0 1-4 0v-.09a1.7 1.7 0 0 0-1.03-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 0 1 0-4h.09A1.7 1.7 0 0 0 4.6 8.94a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34h.01A1.7 1.7 0 0 0 10 3.09V3a2 2 0 0 1 4 0v.09a1.7 1.7 0 0 0 1.03 1.56h.01a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87v.01A1.7 1.7 0 0 0 20.91 10H21a2 2 0 0 1 0 4h-.09A1.7 1.7 0 0 0 19.4 15z" />
              </svg>
            </button>

            {isSettingsOpen && (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-40 rounded-xl border border-slate-200 bg-white shadow-lg py-1 z-20"
              >
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setIsSettingsOpen(false);
                    void handleLogout();
                  }}
                  className="w-full text-left px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 hover:text-[var(--warning)] transition"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="dashboard-shell max-w-6xl mx-auto w-full p-6 py-10">
        {children}
      </main>
    </div>
  );
}
