import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { CityDatalist } from "../components/CityDatalist";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { validateBio } from "../lib/validation";

export function ListingPage() {
  const { profile } = useAuth();
  const [form, setForm] = useState({
    years_experience: 0,
    city: "",
    remote_ok: false,
    rate_rupees: 1000,
    rate_unit: "session" as "session" | "month",
    available: true,
    bio: "",
    coach_role_ids: [] as string[],
  });
  const [roles, setRoles] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  if (!profile) return <Navigate to="/" replace />;
  if (profile.role !== "coach") return <Navigate to="/coaches" replace />;

  useEffect(() => {
    api.get("/coach-roles/", { params: { sport: "soccer" } }).then((r) => setRoles(r.data));
    api
      .get("/me/listing/")
      .then((r) => {
        setForm((f) => ({
          ...f,
          ...r.data,
          coach_role_ids: r.data.coach_role_ids ?? [],
        }));
      })
      .catch(() => {});
  }, []);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    const bioErr = validateBio(form.bio);
    if (bioErr) {
      setError(bioErr);
      return;
    }
    setError(null);
    try {
      await api.put("/me/listing/", form);
      setSaved(true);
    } catch {
      setError("Could not save listing.");
    }
  };

  const toggleRole = (id: string) => {
    setForm((f) => ({
      ...f,
      coach_role_ids: f.coach_role_ids.includes(id)
        ? f.coach_role_ids.filter((x) => x !== id)
        : [...f.coach_role_ids, id],
    }));
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-6">
      <h1 className="text-xl font-semibold">Your listing</h1>
      <form onSubmit={save} className="mt-4 space-y-3 text-sm">
        <CityDatalist
          value={form.city}
          onChange={(c) => setForm((f) => ({ ...f, city: c }))}
          className="w-full rounded-lg border px-3 py-2"
        />
        <input
          type="number"
          min={0}
          max={60}
          value={form.years_experience}
          onChange={(e) => setForm((f) => ({ ...f, years_experience: +e.target.value }))}
          className="w-full rounded-lg border px-3 py-2"
          placeholder="Years experience"
        />
        <input
          type="number"
          min={1}
          value={form.rate_rupees}
          onChange={(e) => setForm((f) => ({ ...f, rate_rupees: +e.target.value }))}
          className="w-full rounded-lg border px-3 py-2"
          placeholder="Rate (₹)"
        />
        <select
          value={form.rate_unit}
          onChange={(e) => setForm((f) => ({ ...f, rate_unit: e.target.value as "session" | "month" }))}
          className="w-full rounded-lg border px-3 py-2"
        >
          <option value="session">Per session</option>
          <option value="month">Per month</option>
        </select>
        <label className="flex gap-2">
          <input
            type="checkbox"
            checked={form.remote_ok}
            onChange={(e) => setForm((f) => ({ ...f, remote_ok: e.target.checked }))}
          />
          Remote OK
        </label>
        <label className="flex gap-2">
          <input
            type="checkbox"
            checked={form.available}
            onChange={(e) => setForm((f) => ({ ...f, available: e.target.checked }))}
          />
          Available on directory
        </label>
        <div>
          <p className="mb-1 font-medium">Roles</p>
          {roles.map((r) => (
            <label key={r.id} className="mr-3 inline-flex gap-1">
              <input
                type="checkbox"
                checked={form.coach_role_ids.includes(r.id)}
                onChange={() => toggleRole(r.id)}
              />
              {r.name}
            </label>
          ))}
        </div>
        <textarea
          rows={5}
          className="w-full rounded-lg border px-3 py-2"
          value={form.bio}
          onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
          placeholder="Bio"
        />
        {error && <p className="text-red-600">{error}</p>}
        {saved && <p className="text-emerald-700">Saved.</p>}
        <button type="submit" className="w-full rounded-lg bg-emerald-700 py-2 text-white">
          Save listing
        </button>
      </form>
    </div>
  );
}
