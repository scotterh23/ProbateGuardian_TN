import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { createSession } from "@/lib/auth";

const schema = z.object({
  token: z.string().min(10),
  name: z.string().min(2),
  password: z.string().min(8),
});

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Name and an 8+ character password are required." }, { status: 400 });
  }

  const invite = await prisma.invite.findUnique({ where: { token: parsed.data.token } });
  if (!invite || invite.usedAt || invite.expiresAt < new Date()) {
    return NextResponse.json({ error: "This invite is invalid or has expired." }, { status: 400 });
  }

  const email = invite.email.toLowerCase();
  const passwordHash = await bcrypt.hash(parsed.data.password, 10);

  const user = await prisma.$transaction(async (tx) => {
    const existing = await tx.user.findUnique({ where: { email } });
    const saved = existing
      ? await tx.user.update({
          where: { id: existing.id },
          data: {
            name: parsed.data.name,
            passwordHash,
            role: existing.role === "ADMIN" ? "ADMIN" : invite.role,
          },
        })
      : await tx.user.create({
          data: {
            email,
            name: parsed.data.name,
            passwordHash,
            role: invite.role,
          },
        });

    await tx.estateMember.upsert({
      where: { estateId_userId: { estateId: invite.estateId, userId: saved.id } },
      update: { role: invite.role },
      create: { estateId: invite.estateId, userId: saved.id, role: invite.role },
    });

    await tx.invite.update({
      where: { id: invite.id },
      data: { usedAt: new Date() },
    });

    return saved;
  });

  const redirectTo = `/estates/${invite.estateId}`;
  const res = NextResponse.json({
    ok: true,
    estateId: invite.estateId,
    redirectTo,
  });
  await createSession(
    {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
    },
    res,
  );
  return res;
}
