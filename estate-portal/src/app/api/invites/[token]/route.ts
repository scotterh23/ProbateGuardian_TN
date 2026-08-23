import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(_: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!token || token.length < 10) {
    return NextResponse.json({ error: "This invite is not valid." }, { status: 404 });
  }

  const invite = await prisma.invite.findUnique({
    where: { token },
    include: {
      estate: { select: { id: true, nickname: true, address: true, city: true, county: true } },
    },
  });
  if (!invite) {
    return NextResponse.json({ error: "This invite is not valid." }, { status: 404 });
  }

  return NextResponse.json({
    email: invite.email,
    role: invite.role,
    used: Boolean(invite.usedAt),
    expired: invite.expiresAt < new Date(),
    estate: invite.estate,
  });
}
