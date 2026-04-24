"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { UserResponse } from "@/lib/api/auth";
import { getAuthToken } from "@/lib/api/client";

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: UserResponse | null) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getAuthToken();
    const storedUser = localStorage.getItem("widenet_user");
    
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Failed to parse cached user", e);
      }
    }
    setIsLoading(false);
  }, []);

  const handleSetUser = (newUser: UserResponse | null) => {
    setUser(newUser);
    if (newUser) {
      localStorage.setItem("widenet_user", JSON.stringify(newUser));
    } else {
      localStorage.removeItem("widenet_user");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        setUser: handleSetUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
