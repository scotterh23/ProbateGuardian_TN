import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

const schema = z.object({
  nickname: z.string().min(2),
  address: z.string().min(3),
  city: z.string().min(2),
  county: z.string().min(2),
  status: z.enum(["LETTERS", "VALUATION", "LISTED", "UNDER_CONTRACT", "CLOSED"]).optional(),
});

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });

  const estates =
    session.role === "ADMIN"
      ? await prisma.estate.findMany({
          orderBy: { updatedAt: "desc" },
          include: { updates: { orderBy: { createdAt: "desc" }, take: 1 } },
        })
      : (
          await prisma.estateMember.findMany({
            where: { userId: session.id },
            include: {
              estate: {
                include: { updates: { orderBy: { createdAt: "desc" }, take: 1 } },
              },
            },
          })
        ).map((m) => m.estate);

  return NextResponse.json({ estates });
}

export async function POST(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "ADMIN") {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const parsed = schema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "Please complete all estate fields." }, { status: 400 });
  }

  const estate = await prisma.estate.create({
    data: {
      ...parsed.data,
      members: { create: { userId: session.id, role: "ADMIN" } },
    },
  });
  return NextResponse.json({ estate });
}
