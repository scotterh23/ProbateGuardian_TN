import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getEstateAccess, getSession } from "@/lib/auth";
import { readUpload } from "@/lib/files";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const update = await prisma.estateUpdate.findUnique({ where: { id } });
  if (!update?.filePath) return NextResponse.json({ error: "Not found." }, { status: 404 });
  const access = await getEstateAccess(session, update.estateId);
  if (!access.allowed) return NextResponse.json({ error: "Not found." }, { status: 404 });
  try {
    const buf = await readUpload(update.filePath);
    return new NextResponse(new Uint8Array(buf), {
      headers: {
        "Content-Type": update.fileMime || "application/octet-stream",
        "Content-Disposition": `inline; filename="${(update.fileName || "file").replace(/"/g, "")}"`,
      },
    });
  } catch {
    return NextResponse.json({ error: "File is missing from storage." }, { status: 404 });
  }
}
