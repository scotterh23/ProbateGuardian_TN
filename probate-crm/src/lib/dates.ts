function asDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const date = new Date(trimmed);
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

export function formatDate(value: string | null | undefined): string | null {
  const date = asDate(value);
  if (!date) return null;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string | null {
  const date = asDate(value);
  if (!date) return null;
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function startOfToday() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

export function isFollowUpDueToday(value: string | null | undefined) {
  const date = asDate(value);
  if (!date) return false;
  const today = startOfToday();
  const day = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  return day.getTime() === today.getTime();
}

export function isFollowUpOverdue(value: string | null | undefined) {
  const date = asDate(value);
  if (!date) return false;
  return date < startOfToday();
}
