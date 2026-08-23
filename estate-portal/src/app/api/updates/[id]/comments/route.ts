import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { canComment, getEstateAccess, getSession } from "@/lib/auth";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const update = await prisma.estateUpdate.findUnique({ where: { id } });
  if (!update) return NextResponse.json({ error: "Update not found." }, { status: 404 });
  const access = await getEstateAccess(session, update.estateId);
  if (!access.allowed) return NextResponse.json({ error: "Not found." }, { status: 404 });
  if (!access.role || !canComment(access.role)) {
    return NextResponse.json(
      { error: "Family members send questions to Probate Guardians instead of public comments." },
      { status: 403 },
    );
  }

  const body = String((await req.json().catch(() => ({}))).body || "").trim();
  if (body.length < 1) {
    return NextResponse.json({ error: "Please write a comment." }, { status: 400 });
  }

  const comment = await prisma.updateComment.create({
    data: { updateId: id, authorId: session.id, body },
  });
  return NextResponse.json({ comment });
}
