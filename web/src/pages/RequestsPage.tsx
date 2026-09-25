import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { HireThread } from "../components/HireThread";
import { ReviewForm } from "../components/ReviewForm";
import { api } from "../lib/api";
import { loadRazorpay, openRazorpayCheckout } from "../lib/razorpay";
import { useAuth } from "../context/AuthContext";
import { formatIst } from "../lib/validation";

type Counterparty = {
  id: string;
  display_name: string;
  mobile?: string;
  email?: string;
  whatsapp_url?: string;
};

type RequestRow = {
  id: string;
  message: string;
  status: string;
  created_at: string;
  payment_status: string | null;
  has_review: boolean;
  counterparty: Counterparty;
};

function errorDetail(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

function RequestCard({
  row,
  role,
  box,
  onChanged,
}: {
  row: RequestRow;
  role: "hirer" | "coach";
  box: "incoming" | "sent";
  onChanged: () => void;
}) {
  const [threadOpen, setThreadOpen] = useState(false);
  const [payError, setPayError] = useState<string | null>(null);
  const [paying, setPaying] = useState(false);
  const threadOpenable = row.status === "pending" || row.status === "accepted";
  const paid = row.payment_status === "captured";
  const canPay = role === "hirer" && row.status === "accepted" && !paid && row.payment_status !== "refunded";
  const canReview = role === "hirer" && row.status === "accepted" && paid && !row.has_review;

  const updateStatus = async (status: string) => {
    await api.patch(`/hire-requests/${row.id}/`, { status });
    onChanged();
  };

  const pay = async () => {
    setPayError(null);
    setPaying(true);
    try {
      await loadRazorpay();
      const { data } = await api.post<{
        order_id: string;
        key_id: string;
        amount_paise: number;
      }>(`/hire-requests/${row.id}/payments/order/`);
      const checkout = await openRazorpayCheckout({
        keyId: data.key_id,
        amountPaise: data.amount_paise,
        orderId: data.order_id,
        description: "Coach hire",
      });
      await api.post(`/hire-requests/${row.id}/payments/verify/`, checkout);
      onChanged();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "";
      if (message === "Checkout closed.") {
        setPayError(null);
      } else {
        setPayError(errorDetail(err, message || "Payment could not be started."));
      }
    } finally {
      setPaying(false);
    }
  };

  return (
    <li className="rounded-xl border bg-white p-4 text-sm shadow-sm">
      <div className="flex justify-between gap-2">
        <span className="font-medium">{row.counterparty.display_name}</span>
        <span className="text-slate-500">{formatIst(row.created_at)} IST</span>
      </div>
      <p className="mt-1 text-slate-600">{row.message}</p>
      <p className="mt-1 capitalize text-slate-500">
        Status: {row.status}
        {row.status === "accepted" && (paid ? " · Paid" : " · Unpaid")}
      </p>
      {row.counterparty.whatsapp_url && (
        <a
          href={row.counterparty.whatsapp_url}
          className="mt-2 inline-block text-emerald-700 underline"
          target="_blank"
          rel="noreferrer"
        >
          WhatsApp {row.counterparty.mobile}
        </a>
      )}
      {role === "coach" && row.status === "pending" && box === "incoming" && (
        <div className="mt-2 flex gap-2">
          <button
            type="button"
            className="rounded bg-emerald-700 px-3 py-1 text-white"
            onClick={() => updateStatus("accepted")}
          >
            Accept
          </button>
          <button
            type="button"
            className="rounded bg-slate-300 px-3 py-1"
            onClick={() => updateStatus("declined")}
          >
            Decline
          </button>
        </div>
      )}
      {role === "hirer" && row.status === "pending" && (
        <button
          type="button"
          className="mt-2 text-sm text-slate-600 underline"
          onClick={() => updateStatus("withdrawn")}
        >
          Withdraw
        </button>
      )}
      {canPay && (
        <button
          type="button"
          disabled={paying}
          className="mt-3 rounded-lg bg-emerald-700 px-3 py-2 text-white disabled:opacity-60"
          onClick={pay}
        >
          {paying ? "Opening checkout…" : "Pay with UPI"}
        </button>
      )}
      {payError && <p className="mt-2 text-sm text-red-600">{payError}</p>}
      {threadOpenable && (
        <button
          type="button"
          className="mt-3 block text-sm text-emerald-800 underline"
          onClick={() => setThreadOpen((open) => !open)}
        >
          {threadOpen ? "Hide messages" : "Messages"}
        </button>
      )}
      {threadOpen && threadOpenable && <HireThread hireRequestId={row.id} />}
      {canReview && (
        <ReviewForm
          hireRequestId={row.id}
          onDone={onChanged}
        />
      )}
      {row.has_review && <p className="mt-2 text-sm text-slate-500">Review submitted.</p>}
    </li>
  );
}

export function RequestsPage() {
  const { profile } = useAuth();
  const [box, setBox] = useState<"incoming" | "sent">(
    profile?.role === "coach" ? "incoming" : "sent",
  );
  const [rows, setRows] = useState<RequestRow[]>([]);

  const load = useCallback(() => {
    if (!profile) return;
    api.get<RequestRow[]>("/me/requests/", { params: { box } }).then((r) => setRows(r.data));
  }, [box, profile]);

  useEffect(() => {
    load();
  }, [load]);

  if (!profile) return <Navigate to="/" replace />;

  return (
    <div className="mx-auto max-w-lg px-4 py-6">
      <h1 className="text-xl font-semibold">Requests</h1>
      {profile.role === "coach" && (
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            className={`rounded-lg px-3 py-1 text-sm ${box === "incoming" ? "bg-emerald-700 text-white" : "bg-slate-200"}`}
            onClick={() => setBox("incoming")}
          >
            Incoming
          </button>
          <button
            type="button"
            className={`rounded-lg px-3 py-1 text-sm ${box === "sent" ? "bg-emerald-700 text-white" : "bg-slate-200"}`}
            onClick={() => setBox("sent")}
          >
            Sent
          </button>
        </div>
      )}
      <ul className="mt-4 space-y-3">
        {rows.map((row) => (
          <RequestCard
            key={row.id}
            row={row}
            role={profile.role}
            box={box}
            onChanged={load}
          />
        ))}
        {rows.length === 0 && <p className="text-slate-500">No requests yet.</p>}
      </ul>
    </div>
  );
}
