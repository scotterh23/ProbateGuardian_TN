import { randomBytes } from "crypto";
import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";
import { publicAppOrigin } from "@/lib/origin";

const schema = z.object({
  estateId: z.string().min(1),
  email: z.string().email(),
  role: z.enum(["EXECUTOR", "HEIR", "ATTORNEY"]),
});

export async function POST(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "ADMIN") {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const parsed = schema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "Email, estate, and role are required." }, { status: 400 });
  }

  const token = randomBytes(24).toString("hex");
  const invite = await prisma.invite.create({
    data: {
      email: parsed.data.email.toLowerCase(),
      role: parsed.data.role,
      estateId: parsed.data.estateId,
      token,
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 14),
      invitedById: session.id,
    },
  });

  const origin = publicAppOrigin(req);
  const invitePath = `/invite/${token}`;
  return NextResponse.json({
    inviteId: invite.id,
    invitePath,
    inviteUrl: `${origin}${invitePath}`,
  });
}
