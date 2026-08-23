import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { createSession } from "@/lib/auth";
import { publicAppOrigin } from "@/lib/origin";

const schema = z.object({
  token: z.string().min(10),
  name: z.string().min(2),
  password: z.string().min(8),
});

async function readPayload(req: Request) {
  const contentType = req.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return schema.safeParse(await req.json().catch(() => null));
  }
  const form = await req.formData().catch(() => null);
  if (!form) return schema.safeParse(null);
  return schema.safeParse({
    token: form.get("token"),
    name: form.get("name"),
    password: form.get("password"),
  });
}

function fail(req: Request, token: string | undefined, message: string, wantsJson: boolean) {
  if (wantsJson) {
    return NextResponse.json({ error: message }, { status: 400 });
  }
  const origin = publicAppOrigin(req);
  const path = token ? `/invite/${token}` : "/invite/missing";
  const url = new URL(path, origin);
  url.searchParams.set("error", message);
  return NextResponse.redirect(url, 303);
}

export async function POST(req: Request) {
  const wantsJson = (req.headers.get("content-type") || "").includes("application/json");
  const parsed = await readPayload(req);
  if (!parsed.success) {
    return fail(req, undefined, "Name and an 8+ character password are required.", wantsJson);
  }

  const invite = await prisma.invite.findUnique({ where: { token: parsed.data.token } });
  if (!invite || invite.usedAt || invite.expiresAt < new Date()) {
    return fail(req, parsed.data.token, "This invite is invalid or has expired.", wantsJson);
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

  const origin = publicAppOrigin(req);
  const redirectTo = `/estates/${invite.estateId}`;
  const res = wantsJson
    ? NextResponse.json({ ok: true, estateId: invite.estateId, redirectTo })
    : NextResponse.redirect(new URL(redirectTo, origin), 303);

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
