import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ReviewForm } from "../components/ReviewForm";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { formatIst, formatRate, formatRating, validateMessage } from "../lib/validation";

type Detail = {
  id: string;
  coach: { id: string; display_name: string };
  bio: string;
  city: string;
  rate_rupees: number;
  rate_unit: "session" | "month";
  rating_avg: number | null;
  rating_count: number;
};

type PublicReview = {
  id: string;
  rating: number;
  body: string;
  created_at: string;
  hirer_display_name: string;
};

type ReviewsPayload = {
  rating_avg: number | null;
  rating_count: number;
  eligible_hire_request_id: string | null;
  reviews: PublicReview[];
};

export function CoachDetailPage() {
  const { id } = useParams();
  const { profile } = useAuth();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [reviews, setReviews] = useState<ReviewsPayload | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const loadReviews = () => {
    if (!id) return;
    api.get<ReviewsPayload>(`/coaches/${id}/reviews/`).then((r) => setReviews(r.data)).catch(() => setReviews(null));
  };

  useEffect(() => {
    if (!id) return;
    api.get<Detail>(`/coaches/${id}/`).then((r) => setDetail(r.data)).catch(() => setDetail(null));
    loadReviews();
  }, [id]);

  const sendRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) {
      navigate("/");
      return;
    }
    const msgErr = validateMessage(message);
    if (msgErr) {
      setError(msgErr);
      return;
    }
    setError(null);
    try {
      await api.post("/hire-requests/", { listing_id: detail!.id, message });
      setSent(true);
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(d ?? "Could not send request.");
    }
  };

  if (!detail) return <p className="p-4 text-sm">Loading…</p>;

  return (
    <div className="mx-auto max-w-lg px-4 py-6">
      <Link to="/coaches" className="text-sm text-emerald-700">← Directory</Link>
      <h1 className="mt-2 text-xl font-semibold">{detail.coach.display_name}</h1>
      <p className="text-sm text-slate-600">{detail.city}</p>
      <p className="mt-1">{formatRate(detail.rate_rupees, detail.rate_unit)}</p>
      <p className="mt-1 text-sm text-slate-600">
        {formatRating(reviews?.rating_avg ?? detail.rating_avg, reviews?.rating_count ?? detail.rating_count)}
      </p>
      <p className="mt-4 text-sm leading-relaxed">{detail.bio}</p>
      <section className="mt-6">
        <h2 className="text-sm font-semibold">Reviews</h2>
        <ul className="mt-2 space-y-3">
          {(reviews?.reviews ?? []).map((review) => (
            <li key={review.id} className="rounded-lg border bg-white p-3 text-sm">
              <p className="font-medium">
                {review.hirer_display_name} · {review.rating} ★
              </p>
              <p className="text-slate-400">{formatIst(review.created_at)} IST</p>
              <p className="mt-1 text-slate-700">{review.body}</p>
            </li>
          ))}
          {(reviews?.reviews.length ?? 0) === 0 && (
            <li className="text-sm text-slate-500">No reviews yet.</li>
          )}
        </ul>
        {reviews?.eligible_hire_request_id && (
          <ReviewForm hireRequestId={reviews.eligible_hire_request_id} onDone={loadReviews} />
        )}
      </section>
      {profile?.role === "hirer" && !sent && (
        <form onSubmit={sendRequest} className="mt-6 space-y-2">
          <textarea
            rows={4}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="Your message to the coach"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" className="w-full rounded-lg bg-emerald-700 py-2 text-white text-sm">
            Send hire request
          </button>
        </form>
      )}
      {sent && (
        <p className="mt-4 text-sm text-emerald-700">
          Request sent. <Link to="/requests">View inbox</Link>
        </p>
      )}
    </div>
  );
}
