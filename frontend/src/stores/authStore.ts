import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  username: string;
  email: string;
  mfa_enabled: boolean;
  incomplete_mfa?: boolean;
}

interface AuthStore {
  token: string | null;
  user: User | null;
  mfaRequired: boolean;
  tempToken: string | null;
  backupCodes: string[] | null;
  setAuth: (token: string, user: User, backupCodes?: string[]) => void;
  setMfaPending: (token: string, user: User) => void;
  completeMfa: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuth = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      token: null,
      user: null,
      mfaRequired: false,
      tempToken: null,
      backupCodes: null,

      // Actions
      setAuth: (token: string, user: User, backupCodes?: string[]) => {
        console.log('[AUTH] Setting auth:', { 
          user: user?.username || 'unknown', 
          mfa_enabled: user?.mfa_enabled || false 
        });
        set({ 
          token, 
          user, 
          mfaRequired: false, 
          tempToken: null, 
          backupCodes: backupCodes || null 
        });
      },

      setMfaPending: (token: string, user: User) => {
        console.log('[AUTH] Setting MFA pending for user:', user.username);
        set({ 
          token: null, 
          user, 
          mfaRequired: true, 
          tempToken: token, 
          backupCodes: null 
        });
      },

      completeMfa: (token: string, user: User) => {
        console.log('[AUTH] Completing MFA for user:', user.username);
        set({ 
          token, 
          user, 
          mfaRequired: false, 
          tempToken: null, 
          backupCodes: null 
        });
      },

      logout: () => {
        console.log('[AUTH] Logging out');
        set({ 
          token: null, 
          user: null, 
          mfaRequired: false, 
          tempToken: null, 
          backupCodes: null 
        });
      },
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({ 
        token: state.token, 
        user: state.user 
      }), // Only persist token and user, not temporary MFA states
    }
  )
);
