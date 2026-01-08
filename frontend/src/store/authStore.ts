import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name?: string;
  role: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      login: (accessToken, refreshToken, user) =>
        set({ accessToken, refreshToken, user, isAuthenticated: true }),
      logout: () =>
        set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false }),
      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
