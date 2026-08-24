import { Resend } from "resend";

const FROM =
  process.env.INVITE_FROM_EMAIL || "Probate Guardians <portal@probateguardians.com>";
const TO = process.env.INTRO_TO_EMAIL || "portal@probateguardians.com";

export async function sendVendorIntroEmail(payload: {
  vendorName: string;
  vendorCategory: string;
  requesterName: string;
  requesterEmail: string;
  requesterRole: string;
  estateName: string;
  estateAddress: string;
}): Promise<{ sent: boolean; reason?: string }> {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return { sent: false, reason: "missing_api_key" };

  const resend = new Resend(apiKey);
  const { error } = await resend.emails.send({
    from: FROM,
    to: TO,
    replyTo: payload.requesterEmail,
    subject: `Vendor intro requested: ${payload.vendorName} — ${payload.estateName}`,
    text: [
      `${payload.requesterName} (${payload.requesterRole}) asked for an introduction.`,
      "",
      `Vendor: ${payload.vendorName} (${payload.vendorCategory})`,
      `Estate: ${payload.estateName}`,
      `Property: ${payload.estateAddress}`,
      `Requester email: ${payload.requesterEmail}`,
    ].join("\n"),
  });

  if (error) return { sent: false, reason: error.message };
  return { sent: true };
}
