"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { logout } from "@/lib/api/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

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
    { name: "Profile", path: "/dashboard/profile" },
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
          <span className="text-sm font-semibold text-slate-700 hidden sm:block">
            {user.name}
          </span>
          <button 
            onClick={handleLogout}
            className="text-sm font-semibold text-slate-500 hover:text-[var(--warning)] transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="dashboard-shell max-w-6xl mx-auto w-full p-6 py-10">
        {children}
      </main>
    </div>
  );
}
