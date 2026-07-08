import { createContext, useContext, useState } from "react";
import { setToken, clearToken, getToken } from "../api/client";

const AuthContext = createContext(null);

const BUSINESS_NAME_KEY = "business_name";

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(!!getToken());
  const [businessName, setBusinessName] = useState(
    () => localStorage.getItem(BUSINESS_NAME_KEY) || ""
  );

  function login(token, name) {
    setToken(token);
    localStorage.setItem(BUSINESS_NAME_KEY, name || "");
    setBusinessName(name || "");
    setIsAuthenticated(true);
  }

  function logout() {
    clearToken();
    localStorage.removeItem(BUSINESS_NAME_KEY);
    setBusinessName("");
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, businessName, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
