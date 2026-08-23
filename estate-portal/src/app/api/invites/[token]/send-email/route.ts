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

  return NextResponse.json({
    sent: result.sent,
    reason: result.reason,
    to: invite.email,
    inviteUrl,
    message:
      "Email sending from the portal is not connected yet. Copy the invite link and send it directly.",
  });
}
