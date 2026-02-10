import React, { createContext, useContext, useState, useCallback } from "react";

interface User {
  username: string;
  email: string;
  mfa_enabled: boolean;
}

interface AuthState {
  token: string | null;
  user: User | null;
  mfaRequired: boolean;
  tempToken: string | null; // token before MFA verification
}

interface AuthContextType extends AuthState {
  setAuth: (token: string, user: User) => void;
  setMfaPending: (token: string, user: User) => void;
  completeMfa: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    token: null,
    user: null,
    mfaRequired: false,
    tempToken: null,
  });

  const setAuth = useCallback((token: string, user: User) => {
    setState({ token, user, mfaRequired: false, tempToken: null });
  }, []);

  const setMfaPending = useCallback((token: string, user: User) => {
    setState({ token: null, user, mfaRequired: true, tempToken: token });
  }, []);

  const completeMfa = useCallback((token: string, user: User) => {
    setState({ token, user, mfaRequired: false, tempToken: null });
  }, []);

  const logout = useCallback(() => {
    setState({ token: null, user: null, mfaRequired: false, tempToken: null });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, setAuth, setMfaPending, completeMfa, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
