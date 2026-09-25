import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api, setTokens } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import type { HirerKind, UserRole } from "../lib/validation";

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-600 focus:outline-none";

export function HomePage() {
  const { profile, login } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("hirer");
  const [displayName, setDisplayName] = useState("");
  const [mobile, setMobile] = useState("");
  const [hirerKind, setHirerKind] = useState<HirerKind>("player");
  const [clubName, setClubName] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (profile) {
    return <Navigate to={profile.role === "coach" ? "/listing" : "/coaches"} replace />;
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        const { data } = await api.post("/auth/register/", {
          email,
          password,
          role,
          display_name: displayName,
          mobile,
          hirer_kind: role === "hirer" ? hirerKind : null,
          club_name: role === "hirer" && hirerKind === "club" ? clubName : null,
        });
        setTokens(data.access, data.refresh);
        window.location.reload();
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Something went wrong.");
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-8">
      <h1 className="text-2xl font-semibold text-emerald-800">ForHire India</h1>
      <p className="mt-1 text-sm text-slate-600">Find soccer coaches across India.</p>
      <div className="mt-6 flex gap-2">
        <button
          type="button"
          className={`flex-1 rounded-lg py-2 text-sm ${mode === "login" ? "bg-emerald-700 text-white" : "bg-slate-200"}`}
          onClick={() => setMode("login")}
        >
          Log in
        </button>
        <button
          type="button"
          className={`flex-1 rounded-lg py-2 text-sm ${mode === "register" ? "bg-emerald-700 text-white" : "bg-slate-200"}`}
          onClick={() => setMode("register")}
        >
          Sign up
        </button>
      </div>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={inputClass}
        />
        <input
          type="password"
          required
          minLength={8}
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={inputClass}
        />
        {mode === "register" && (
          <>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className={inputClass}
            >
              <option value="hirer">I want to hire a coach</option>
              <option value="coach">I am a coach</option>
            </select>
            <input
              placeholder="Display name"
              required
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className={inputClass}
            />
            <input
              placeholder="Mobile (10 digits)"
              required
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
              className={inputClass}
            />
            {role === "hirer" && (
              <>
                <select
                  value={hirerKind}
                  onChange={(e) => setHirerKind(e.target.value as HirerKind)}
                  className={inputClass}
                >
                  <option value="player">Player</option>
                  <option value="parent">Parent</option>
                  <option value="club">Club</option>
                </select>
                {hirerKind === "club" && (
                  <input
                    placeholder="Club name"
                    required
                    value={clubName}
                    onChange={(e) => setClubName(e.target.value)}
                    className={inputClass}
                  />
                )}
              </>
            )}
          </>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          className="w-full rounded-lg bg-emerald-700 py-2.5 text-sm font-medium text-white"
        >
          {mode === "login" ? "Log in" : "Create account"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm">
        <Link to="/coaches" className="text-emerald-700 underline">Browse coaches</Link>
      </p>
    </div>
  );
}
