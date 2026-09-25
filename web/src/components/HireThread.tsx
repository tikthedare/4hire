import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { formatIst } from "../lib/validation";

type ChatMessage = {
  id: string;
  sender_id: string;
  sender_display_name: string;
  body: string;
  created_at: string;
};

const POLL_MS = 8000;

export function HireThread({ hireRequestId }: { hireRequestId: string }) {
  const { profile } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const afterRef = useRef<string | null>(null);

  useEffect(() => {
    let stopped = false;
    let timer = 0;

    const schedule = () => {
      window.clearTimeout(timer);
      if (stopped || document.visibilityState === "hidden") return;
      timer = window.setTimeout(poll, POLL_MS);
    };

    const poll = async () => {
      if (stopped || document.visibilityState === "hidden") return;
      try {
        const params: Record<string, string> = {};
        if (afterRef.current) params.after = afterRef.current;
        const { data } = await api.get<ChatMessage[]>(
          `/hire-requests/${hireRequestId}/messages/`,
          { params },
        );
        if (!stopped && data.length) {
          setMessages((prev) => {
            const seen = new Set(prev.map((item) => item.id));
            const next = [...prev];
            for (const item of data) {
              if (!seen.has(item.id)) next.push(item);
            }
            return next;
          });
          afterRef.current = data[data.length - 1].created_at;
        }
      } catch {
        /* keep the thread quiet and try again on the next tick */
      }
      schedule();
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") poll();
    };
    document.addEventListener("visibilitychange", onVisibility);
    poll();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [hireRequestId]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = body.trim();
    if (!text || text.length > 2000) {
      setError("Message must be 1–2000 characters.");
      return;
    }
    setError(null);
    try {
      const { data } = await api.post<ChatMessage>(`/hire-requests/${hireRequestId}/messages/`, {
        body: text,
      });
      setMessages((prev) => (prev.some((item) => item.id === data.id) ? prev : [...prev, data]));
      afterRef.current = data.created_at;
      setBody("");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not send message.");
    }
  };

  return (
    <div className="mt-3 rounded-lg bg-slate-50 p-3">
      <ul className="max-h-48 space-y-2 overflow-y-auto">
        {messages.map((message) => (
          <li key={message.id} className="text-sm">
            <span className="font-medium">
              {message.sender_id === profile?.id ? "You" : message.sender_display_name}
            </span>
            <span className="text-slate-400"> · {formatIst(message.created_at)} IST</span>
            <p className="text-slate-700">{message.body}</p>
          </li>
        ))}
        {messages.length === 0 && <li className="text-sm text-slate-500">No messages yet.</li>}
      </ul>
      <form onSubmit={send} className="mt-2 flex gap-2">
        <input
          value={body}
          onChange={(e) => setBody(e.target.value)}
          maxLength={2000}
          placeholder="Message"
          className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-sm"
        />
        <button type="submit" className="rounded-lg bg-emerald-700 px-3 py-2 text-sm text-white">
          Send
        </button>
      </form>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
