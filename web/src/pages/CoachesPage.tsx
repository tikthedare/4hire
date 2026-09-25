import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CityDatalist } from "../components/CityDatalist";
import { api } from "../lib/api";
import { formatRate, formatRating } from "../lib/validation";

type ListingCard = {
  id: string;
  coach: { id: string; display_name: string };
  city: string;
  remote_ok: boolean;
  rate_rupees: number;
  rate_unit: "session" | "month";
  coach_role_slugs: string[];
  rating_avg: number | null;
  rating_count: number;
};

export function CoachesPage() {
  const [items, setItems] = useState<ListingCard[]>([]);
  const [city, setCity] = useState("");
  const [coachRole, setCoachRole] = useState("");
  const [remote, setRemote] = useState(false);
  const [roles, setRoles] = useState<{ slug: string; name: string }[]>([]);

  useEffect(() => {
    api.get("/coach-roles/", { params: { sport: "soccer" } }).then((r) => setRoles(r.data));
  }, []);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (city.trim()) params.city = city.trim();
    if (coachRole) params.coach_role = coachRole;
    if (remote) params.remote = "true";
    api.get<ListingCard[]>("/coaches/", { params }).then((r) => setItems(r.data));
  }, [city, coachRole, remote]);

  return (
    <div className="mx-auto max-w-lg px-4 py-6">
      <h1 className="text-xl font-semibold">Coach directory</h1>
      <div className="mt-4 space-y-2">
        <CityDatalist value={city} onChange={setCity} className="w-full rounded-lg border px-3 py-2 text-sm" />
        <select
          value={coachRole}
          onChange={(e) => setCoachRole(e.target.value)}
          className="w-full rounded-lg border px-3 py-2 text-sm"
        >
          <option value="">All roles</option>
          {roles.map((r) => (
            <option key={r.slug} value={r.slug}>{r.name}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={remote} onChange={(e) => setRemote(e.target.checked)} />
          Remote OK
        </label>
      </div>
      <ul className="mt-6 space-y-3">
        {items.map((l) => (
          <li key={l.id} className="rounded-xl border bg-white p-4 shadow-sm">
            <Link to={`/coaches/${l.coach.id}`} className="font-medium text-emerald-800">
              {l.coach.display_name}
            </Link>
            <p className="text-sm text-slate-600">{l.city}{l.remote_ok ? " · Remote OK" : ""}</p>
            <p className="text-sm">{formatRate(l.rate_rupees, l.rate_unit)}</p>
            <p className="text-sm text-slate-600">{formatRating(l.rating_avg, l.rating_count)}</p>
          </li>
        ))}
        {items.length === 0 && <p className="text-sm text-slate-500">No coaches match your filters.</p>}
      </ul>
    </div>
  );
}
