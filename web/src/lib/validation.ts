export type UserRole = "hirer" | "coach";
export type HirerKind = "player" | "parent" | "club";
export type RateUnit = "session" | "month";

const MOBILE_RE = /^[6-9]\d{9}$/;

export function validateMobile(mobile: string): string | null {
  const trimmed = mobile.trim();
  if (!MOBILE_RE.test(trimmed)) {
    return "Enter a valid 10-digit Indian mobile number starting with 6–9.";
  }
  return null;
}

export function validateBio(bio: string): string | null {
  const trimmed = bio.trim();
  if (trimmed.length < 1) return "Bio is required.";
  if (trimmed.length > 500) return "Bio must be at most 500 characters.";
  return null;
}

export function validateMessage(message: string): string | null {
  const trimmed = message.trim();
  if (trimmed.length < 1) return "Message is required.";
  if (trimmed.length > 1000) return "Message must be at most 1000 characters.";
  return null;
}

export function formatRate(rateRupees: number, unit: RateUnit): string {
  return `₹${rateRupees.toLocaleString("en-IN")} / ${unit}`;
}

export function formatIst(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
}

export function formatRating(avg: number | null, count: number): string {
  if (!count || avg == null) return "No reviews yet";
  const label = count === 1 ? "review" : "reviews";
  return `${avg.toFixed(1)} ★ · ${count} ${label}`;
}
