'use client';
import { create } from 'zustand';
import { api } from '@/lib/api';

type User = { id: string; email: string; name?: string | null; planTier: string };

type AuthState = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  setToken: (token: string) => Promise<void>;
  loadMe: () => Promise<void>;
  logout: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  user: null,
  ready: false,
  login: async (email, password) => {
    const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    localStorage.setItem('token', data.access_token);
    set({ user: data.user, ready: true });
  },
  register: async (email, password, name) => {
    const data = await api('/auth/register', { method: 'POST', body: JSON.stringify({ email, password, name }) });
    localStorage.setItem('token', data.access_token);
    set({ user: data.user, ready: true });
  },
  setToken: async (token) => {
    localStorage.setItem('token', token);
    const me = await api('/auth/me');
    set({ user: me, ready: true });
  },
  loadMe: async () => {
    try {
      const me = await api('/auth/me');
      set({ user: me, ready: true });
    } catch {
      set({ user: null, ready: true });
    }
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null });
  },
}));
