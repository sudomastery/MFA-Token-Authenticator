import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

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
  backupCodes: string[] | null; // backup codes from MFA setup
}

interface AuthContextType extends AuthState {
  setAuth: (token: string, user: User, backupCodes?: string[]) => void;
  setMfaPending: (token: string, user: User) => void;
  completeMfa: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(() => {
    // Initialize from localStorage on mount
    try {
      const storedToken = localStorage.getItem("auth_token");
      const storedUser = localStorage.getItem("auth_user");
      
      if (storedToken && storedUser) {
        console.log('[AUTH] Restoring auth state from localStorage');
        return {
          token: storedToken,
          user: JSON.parse(storedUser),
          mfaRequired: false,
          tempToken: null,
          backupCodes: null,
        };
      }
    } catch (error) {
      console.error('[AUTH] Failed to restore auth state:', error);
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    }
    
    return {
      token: null,
      user: null,
      mfaRequired: false,
      tempToken: null,
      backupCodes: null,
    };
  });

  // Persist to localStorage whenever token/user changes
  useEffect(() => {
    if (state.token && state.user) {
      console.log('[AUTH] Persisting auth state to localStorage');
      localStorage.setItem("auth_token", state.token);
      localStorage.setItem("auth_user", JSON.stringify(state.user));
    } else {
      console.log('[AUTH] Clearing auth state from localStorage');
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    }
  }, [state.token, state.user]);

  const setAuth = useCallback((token: string, user: User, backupCodes?: string[]) => {
    console.log('[AUTH] Setting auth:', { user: user.username, mfa_enabled: user.mfa_enabled });
    setState({ token, user, mfaRequired: false, tempToken: null, backupCodes: backupCodes || null });
  }, []);

  const setMfaPending = useCallback((token: string, user: User) => {
    console.log('[AUTH] Setting MFA pending for user:', user.username);
    setState({ token: null, user, mfaRequired: true, tempToken: token, backupCodes: null });
  }, []);

  const completeMfa = useCallback((token: string, user: User) => {
    console.log('[AUTH] Completing MFA for user:', user.username);
    setState({ token, user, mfaRequired: false, tempToken: null, backupCodes: null });
  }, []);

  const logout = useCallback(() => {
    console.log('[AUTH] Logging out');
    setState({ token: null, user: null, mfaRequired: false, tempToken: null, backupCodes: null });
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
