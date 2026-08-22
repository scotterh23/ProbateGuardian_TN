import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getEstateAccess, getSession } from "@/lib/auth";
import { readUpload } from "@/lib/files";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const doc = await prisma.document.findUnique({ where: { id } });
  if (!doc) return NextResponse.json({ error: "Not found." }, { status: 404 });
  const access = await getEstateAccess(session, doc.estateId);
  if (!access.allowed) return NextResponse.json({ error: "Not found." }, { status: 404 });

  const buf = await readUpload(doc.filePath);
  return new NextResponse(new Uint8Array(buf), {
    headers: {
      "Content-Type": doc.fileMime,
      "Content-Disposition": `inline; filename="${doc.fileName.replace(/"/g, "")}"`,
    },
  });
}
