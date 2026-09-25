import { useState } from "react";
import { api } from "../lib/api";

export function ReviewForm({
  hireRequestId,
  onDone,
}: {
  hireRequestId: string;
  onDone: () => void;
}) {
  const [rating, setRating] = useState(5);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = body.trim();
    if (!text || text.length > 500) {
      setError("Review must be 1–500 characters.");
      return;
    }
    setError(null);
    try {
      await api.post(`/hire-requests/${hireRequestId}/review/`, { rating, body: text });
      setBody("");
      onDone();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not save review.");
    }
  };

  return (
    <form onSubmit={submit} className="mt-3 space-y-2">
      <label className="block text-sm">
        Rating
        <select
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
          className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
        >
          {[5, 4, 3, 2, 1].map((value) => (
            <option key={value} value={value}>
              {value} star{value === 1 ? "" : "s"}
            </option>
          ))}
        </select>
      </label>
      <textarea
        rows={3}
        maxLength={500}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="How was the hire?"
        className="w-full rounded-lg border px-3 py-2 text-sm"
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button type="submit" className="rounded-lg bg-emerald-700 px-3 py-2 text-sm text-white">
        Submit review
      </button>
    </form>
  );
}
