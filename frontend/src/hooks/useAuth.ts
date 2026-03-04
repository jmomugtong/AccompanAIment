import { useState, useCallback, useEffect } from "react";
import { apiClient } from "../services/api";

const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";

/**
 * Minimal user profile stored alongside the JWT.
 */
export interface AuthUser {
  id: string;
  email: string;
  username: string;
}

/**
 * State exposed by the useAuth hook.
 */
export interface AuthState {
  /** Whether the user is currently authenticated. */
  isAuthenticated: boolean;
  /** The authenticated user's profile, or null. */
  user: AuthUser | null;
  /** Whether a login or registration request is in flight. */
  loading: boolean;
  /** Last authentication error message, or null. */
  error: string | null;
}

/**
 * Actions exposed by the useAuth hook.
 */
export interface AuthActions {
  /** Authenticate with email and password. */
  login: (email: string, password: string) => Promise<void>;
  /** Create a new account and log in. */
  register: (
    email: string,
    username: string,
    password: string,
  ) => Promise<void>;
  /** Clear stored credentials and log out. */
  logout: () => void;
}

interface LoginResponse {
  access_token: string;
  user: AuthUser;
}

/**
 * Read persisted auth state from localStorage on mount.
 */
function loadPersistedState(): { user: AuthUser | null; token: string | null } {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const raw = localStorage.getItem(USER_KEY);
    const user = raw ? (JSON.parse(raw) as AuthUser) : null;
    return { token, user };
  } catch {
    return { token: null, user: null };
  }
}

/**
 * Hook that manages authentication state (JWT + user profile).
 *
 * Persists the token and user in localStorage so sessions survive
 * page reloads. Automatically clears state on 401 responses (handled
 * by the Axios interceptor in api.ts).
 */
export function useAuth(): [AuthState, AuthActions] {
  const persisted = loadPersistedState();

  const [user, setUser] = useState<AuthUser | null>(persisted.user);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = user !== null && localStorage.getItem(TOKEN_KEY) !== null;

  // Watch for token removal by the Axios interceptor (e.g. on 401).
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === TOKEN_KEY && e.newValue === null) {
        setUser(null);
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<LoginResponse>("/auth/login", {
        email,
        password,
      });

      const { access_token, user: userData } = response.data;
      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
      setUser(userData);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Login failed. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(
    async (email: string, username: string, password: string) => {
      setLoading(true);
      setError(null);

      try {
        const response = await apiClient.post<LoginResponse>("/auth/register", {
          email,
          username,
          password,
        });

        const { access_token, user: userData } = response.data;
        localStorage.setItem(TOKEN_KEY, access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(userData));
        setUser(userData);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Registration failed. Please try again.";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setError(null);
  }, []);

  const state: AuthState = { isAuthenticated, user, loading, error };
  const actions: AuthActions = { login, register, logout };

  return [state, actions];
}
