import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { canAskQuestion, getEstateAccess, getSession } from "@/lib/auth";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed) return NextResponse.json({ error: "Not found." }, { status: 404 });
  if (!access.role || !canAskQuestion(access.role)) {
    return NextResponse.json(
      { error: "Questions are for heirs. The team posts updates instead." },
      { status: 403 },
    );
  }

  const body = String((await req.json().catch(() => ({}))).body || "").trim();
  if (body.length < 4) {
    return NextResponse.json({ error: "Please write a short question." }, { status: 400 });
  }
  if (body.length > 2000) {
    return NextResponse.json({ error: "Please keep questions under 2,000 characters." }, { status: 400 });
  }

  const question = await prisma.estateQuestion.create({
    data: { estateId: id, authorId: session.id, body },
  });
  return NextResponse.json({ question });
}
