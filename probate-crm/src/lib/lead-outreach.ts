import { activityKind, type Lead, type LeadActivity } from "@/lib/types";

function lastActivityAt(activities: LeadActivity[] | undefined, kinds: string[]) {
  const matches = (activities ?? []).filter((a) => kinds.includes(activityKind(a)));
  if (!matches.length) return null;
  return matches.reduce((latest, item) => (item.created_at > latest ? item.created_at : latest), matches[0].created_at);
}

export function outreachSummary(lead: Lead) {
  const activities = lead.lead_activities ?? [];
  const calls = activities.filter((a) => activityKind(a) === "call");
  const emails = activities.filter((a) => activityKind(a) === "email");
  const mailers = activities.filter((a) => ["mailer", "mail"].includes(activityKind(a)));
  return {
    callCount: calls.length,
    lastCalledAt: lastActivityAt(activities, ["call"]),
    emailCount: emails.length,
    lastEmailAt: lastActivityAt(activities, ["email"]),
    mailerCount: mailers.length,
    lastMailerAt: lastActivityAt(activities, ["mailer", "mail"]),
    needsMailer:
      lead.status === "needs_mailer" ||
      (lead.notes ?? "").includes("MAILER QUEUE") ||
      (lead.notes_summary ?? "").includes("MAILER QUEUE"),
  };
}
