import { Resend } from "resend";
import { ROLE_LABEL } from "@/lib/status";
import { UserRole } from "@prisma/client";

export type InviteEmailPayload = {
  to: string;
  inviteUrl: string;
  role: string;
  estateName: string;
};

const FROM =
  process.env.INVITE_FROM_EMAIL || "Probate Guardians <portal@probateguardians.com>";

export async function sendInviteEmail(payload: InviteEmailPayload): Promise<{
  sent: boolean;
  reason?: string;
  id?: string;
}> {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    return { sent: false, reason: "missing_api_key" };
  }

  const roleLabel = ROLE_LABEL[payload.role as UserRole] || payload.role;
  const resend = new Resend(apiKey);
  const { data, error } = await resend.emails.send({
    from: FROM,
    to: payload.to,
    subject: `You're invited to the ${payload.estateName} estate portal`,
    text: [
      `You've been invited to the Probate Guardians Estate Portal as ${roleLabel} for ${payload.estateName}.`,
      "",
      "Open this link to create your access (name and password):",
      payload.inviteUrl,
      "",
      "The link expires in 14 days. If you weren't expecting this, you can ignore it.",
      "",
      "Probate Guardians TN",
    ].join("\n"),
    html: `<div style="font-family:Georgia,serif;line-height:1.6;color:#1c2e28;max-width:560px">
      <p>You've been invited to the <strong>Probate Guardians Estate Portal</strong> as <strong>${escapeHtml(roleLabel)}</strong> for <strong>${escapeHtml(payload.estateName)}</strong>.</p>
      <p><a href="${escapeHtml(payload.inviteUrl)}" style="display:inline-block;background:#0f2922;color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px;font-weight:700">Create your access</a></p>
      <p style="font-size:14px;color:#5c6f66">Or paste this link:<br /><a href="${escapeHtml(payload.inviteUrl)}">${escapeHtml(payload.inviteUrl)}</a></p>
      <p style="font-size:14px;color:#5c6f66">The link expires in 14 days. If you weren't expecting this, you can ignore it.</p>
      <p>Probate Guardians TN</p>
    </div>`,
  });

  if (error) {
    return { sent: false, reason: error.message };
  }
  return { sent: true, id: data?.id };
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
