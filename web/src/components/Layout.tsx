import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { profile, logout, loading } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <nav className="mx-auto flex max-w-lg items-center justify-between px-4 py-3 text-sm">
          <Link to="/" className="font-semibold text-emerald-800">ForHire</Link>
          <div className="flex gap-3">
            <Link to="/coaches">Coaches</Link>
            {profile?.role === "coach" && <Link to="/listing">Listing</Link>}
            {profile && <Link to="/requests">Requests</Link>}
            {!loading && profile && (
              <button type="button" onClick={() => logout()} className="text-slate-600">
                Log out
              </button>
            )}
          </div>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
