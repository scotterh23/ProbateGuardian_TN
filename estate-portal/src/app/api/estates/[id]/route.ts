import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { getEstateAccess, getSession } from "@/lib/auth";

const patchSchema = z.object({
  nickname: z.string().min(2).optional(),
  address: z.string().min(3).optional(),
  city: z.string().min(2).optional(),
  county: z.string().min(2).optional(),
  status: z.enum(["LETTERS", "VALUATION", "LISTED", "UNDER_CONTRACT", "CLOSED"]).optional(),
});

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed) return NextResponse.json({ error: "Not found." }, { status: 404 });

  const estate = await prisma.estate.findUnique({
    where: { id },
    include: {
      members: { include: { user: { select: { id: true, name: true, email: true, role: true } } } },
      updates: {
        orderBy: { createdAt: "desc" },
        include: {
          author: { select: { id: true, name: true, role: true } },
          comments: {
            orderBy: { createdAt: "asc" },
            include: { author: { select: { id: true, name: true, role: true } } },
          },
        },
      },
      documents: {
        orderBy: { createdAt: "desc" },
        include: { uploadedBy: { select: { name: true } } },
      },
    },
  });
  if (!estate) return NextResponse.json({ error: "Not found." }, { status: 404 });
  return NextResponse.json({ estate, accessRole: access.role });
}

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session || session.role !== "ADMIN") {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const { id } = await params;
  const parsed = patchSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid estate update." }, { status: 400 });
  }
  const estate = await prisma.estate.update({ where: { id }, data: parsed.data });
  return NextResponse.json({ estate });
}
