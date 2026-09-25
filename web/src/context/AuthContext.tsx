import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, bootstrapSession, clearTokens, login as apiLogin } from "../lib/api";

export type Profile = {
  id: string;
  role: "hirer" | "coach";
  display_name: string;
  email: string;
  mobile: string;
  hirer_kind?: string | null;
  club_name?: string | null;
};

type AuthContextValue = {
  profile: Profile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    try {
      const { data } = await api.get<Profile>("/me/");
      setProfile(data);
    } catch {
      setProfile(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      await bootstrapSession();
      await refreshProfile();
      setLoading(false);
    })();
  }, [refreshProfile]);

  const login = async (email: string, password: string) => {
    await apiLogin(email, password);
    await refreshProfile();
  };

  const logout = async () => {
    try {
      const refresh = sessionStorage.getItem("forhire_refresh");
      if (refresh) await api.post("/auth/logout/", { refresh });
    } catch {
      /* ignore */
    }
    clearTokens();
    setProfile(null);
  };

  return (
    <AuthContext.Provider value={{ profile, loading, login, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}
