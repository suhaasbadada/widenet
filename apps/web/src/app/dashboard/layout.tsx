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
  const [isDesktopSettingsOpen, setIsDesktopSettingsOpen] = useState(false);
  const [isMobileSettingsOpen, setIsMobileSettingsOpen] = useState(false);
  const desktopSettingsMenuRef = useRef<HTMLDivElement | null>(null);
  const mobileSettingsMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (
        desktopSettingsMenuRef.current &&
        !desktopSettingsMenuRef.current.contains(event.target as Node)
      ) {
        setIsDesktopSettingsOpen(false);
      }

      if (
        mobileSettingsMenuRef.current &&
        !mobileSettingsMenuRef.current.contains(event.target as Node)
      ) {
        setIsMobileSettingsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  useEffect(() => {
    setIsDesktopSettingsOpen(false);
    setIsMobileSettingsOpen(false);
  }, [pathname]);

  const handleLogout = async () => {
    await logout();
    setUser(null);
    router.push("/");
  };

  if (!user) {
    return <div className="page-shell flex items-center justify-center">Loading...</div>;
  }

  const navItems = [
    {
      name: "Resumes",
      path: "/dashboard/resumes",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
    },
    {
      name: "Outreach",
      path: "/dashboard/outreach",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="m22 2-7 20-4-9-9-4Z" />
          <path d="M22 2 11 13" />
        </svg>
      ),
    },
    {
      name: "Answers",
      path: "/dashboard/answers",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
  ];

  const profileActive = pathname.startsWith("/dashboard/profile");

  return (
    <div className="min-h-screen page-shell md:flex">
      <aside className="hidden md:flex md:w-16 lg:w-16 md:flex-col md:justify-between md:sticky md:top-0 md:h-screen bg-white border-r border-slate-200 p-2 md:z-40">
        <div>
          <div className="px-1 py-1.5 flex justify-center">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)] font-bold text-sm" title="Widenet">
              W
            </span>
          </div>

          <nav className="mt-4 flex flex-col items-center gap-1.5">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.path);
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  title={item.name}
                  aria-label={item.name}
                  className={`inline-flex h-9 w-9 items-center justify-center rounded-lg transition ${
                    isActive
                      ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {item.icon}
                  <span className="sr-only">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="pt-2.5 border-t border-slate-200 flex flex-col items-center gap-1.5">
          <button
            type="button"
            onClick={() => router.push("/dashboard/profile")}
            title={user.name || "Profile"}
            className={`inline-flex h-9 w-9 items-center justify-center rounded-lg transition cursor-pointer ${
              profileActive
                ? "text-[var(--accent)] bg-[var(--accent-soft)]"
                : "text-slate-700 hover:text-[var(--accent)] hover:bg-slate-100"
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
            <span className="sr-only">Open profile</span>
          </button>

          <div className="relative" ref={desktopSettingsMenuRef}>
            <button
              type="button"
              aria-label="Open settings menu"
              aria-haspopup="menu"
              aria-expanded={isDesktopSettingsOpen}
              onClick={() => setIsDesktopSettingsOpen((prev) => !prev)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 hover:text-[var(--accent)] hover:bg-slate-100 transition"
              title="Settings"
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
              <span className="sr-only">Settings</span>
            </button>

            {isDesktopSettingsOpen && (
              <div
                role="menu"
                className="absolute left-11 bottom-0 w-44 rounded-xl border border-slate-200 bg-white shadow-lg py-1 z-[70]"
              >
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setIsDesktopSettingsOpen(false);
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
      </aside>

      <div className="flex-1 min-w-0">
        <header className="md:hidden bg-white border-b border-slate-200 sticky top-0 z-10 px-4 py-3 flex items-center justify-between shadow-sm">
          <h1 className="font-display font-bold text-lg tracking-tight text-[var(--accent)]">Widenet</h1>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => router.push("/dashboard/profile")}
              className={`inline-flex items-center gap-2 px-2 py-1 rounded-lg text-sm font-semibold transition cursor-pointer ${
                profileActive
                  ? "text-[var(--accent)] bg-[var(--accent-soft)]"
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
              <span className="max-w-[110px] truncate">{user.name}</span>
            </button>

            <div className="relative" ref={mobileSettingsMenuRef}>
              <button
                type="button"
                aria-label="Open settings menu"
                aria-haspopup="menu"
                aria-expanded={isMobileSettingsOpen}
                onClick={() => setIsMobileSettingsOpen((prev) => !prev)}
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

              {isMobileSettingsOpen && (
                <div
                  role="menu"
                  className="absolute right-0 mt-2 w-40 rounded-xl border border-slate-200 bg-white shadow-lg py-1 z-[70]"
                >
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setIsMobileSettingsOpen(false);
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

        <nav className="md:hidden bg-white border-b border-slate-200 px-3 py-2 flex gap-1 overflow-x-auto">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`shrink-0 px-3 py-2 rounded-lg text-sm font-semibold transition ${
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

        <main className="dashboard-shell w-full p-6 md:p-8 lg:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}
