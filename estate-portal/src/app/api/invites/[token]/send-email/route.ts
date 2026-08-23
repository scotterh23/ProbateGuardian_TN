import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";
import { sendInviteEmail } from "@/lib/invite-email";
import { publicAppOrigin } from "@/lib/origin";

export const runtime = "nodejs";

export async function POST(req: Request, { params }: { params: Promise<{ token: string }> }) {
  const session = await getSession();
  if (!session || session.role !== "ADMIN") {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const { token } = await params;
  const invite = await prisma.invite.findUnique({
    where: { token },
    include: { estate: { select: { nickname: true } } },
  });
  if (!invite || invite.usedAt || invite.expiresAt < new Date()) {
    return NextResponse.json({ error: "This invite is no longer valid." }, { status: 400 });
  }

  const inviteUrl = `${publicAppOrigin(req)}/invite/${invite.token}`;
  const result = await sendInviteEmail({
    to: invite.email,
    inviteUrl,
    role: invite.role,
    estateName: invite.estate.nickname,
  });

  if (!result.sent) {
    const message =
      result.reason === "missing_api_key"
        ? "Email is not configured. Add RESEND_API_KEY on Vercel, then try again."
        : `Could not send email (${result.reason || "unknown error"}). Copy the link and send it directly.`;
    return NextResponse.json({ sent: false, reason: result.reason, to: invite.email, inviteUrl, message }, { status: 500 });
  }

  return NextResponse.json({
    sent: true,
    to: invite.email,
    inviteUrl,
    message: `Invite email sent to ${invite.email}.`,
  });
}
