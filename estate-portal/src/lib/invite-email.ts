export type InviteEmailPayload = {
  to: string;
  inviteUrl: string;
  role: string;
  estateName: string;
};

/**
 * Placeholder for portal-sent invite email.
 * Returns skipped until an email provider is wired (Resend, Postmark, etc.).
 */
export async function sendInviteEmail(_payload: InviteEmailPayload): Promise<{
  sent: boolean;
  reason: "not_configured";
}> {
  return { sent: false, reason: "not_configured" };
}
