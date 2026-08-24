import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { canUpdateSnapshot, getEstateAccess, getSession } from "@/lib/auth";
import { getUploadedFile, MAX_UPLOAD_BYTES, readUpload, removeUpload, saveUpload } from "@/lib/files";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed) return NextResponse.json({ error: "Not found." }, { status: 404 });
  const estate = await prisma.estate.findUnique({ where: { id } });
  if (!estate?.settlementFilePath) {
    return NextResponse.json({ error: "No closing document uploaded." }, { status: 404 });
  }
  try {
    const buf = await readUpload(estate.settlementFilePath);
    return new NextResponse(new Uint8Array(buf), {
      headers: {
        "Content-Type": estate.settlementFileMime || "application/octet-stream",
        "Content-Disposition": `inline; filename="${(estate.settlementFileName || "closing-docs").replace(/"/g, "")}"`,
      },
    });
  } catch {
    return NextResponse.json({ error: "File is missing from storage." }, { status: 404 });
  }
}

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed || !access.role || !canUpdateSnapshot(access.role)) {
    return NextResponse.json({ error: "Only the executor and Probate Guardians can upload closing documents." }, { status: 403 });
  }
  const form = await req.formData().catch(() => null);
  const file = form ? getUploadedFile(form) : null;
  if (!file) return NextResponse.json({ error: "Choose a file to upload." }, { status: 400 });
  if (file.size > MAX_UPLOAD_BYTES) {
    return NextResponse.json({ error: "Files must be 12MB or smaller." }, { status: 400 });
  }
  const estate = await prisma.estate.findUnique({ where: { id } });
  if (!estate) return NextResponse.json({ error: "Not found." }, { status: 404 });
  if (estate.settlementFilePath) await removeUpload(estate.settlementFilePath);
  const saved = await saveUpload(file);
  await prisma.estate.update({
    where: { id },
    data: {
      settlementFileName: saved.fileName,
      settlementFilePath: saved.storedName,
      settlementFileMime: saved.mime,
    },
  });
  return NextResponse.json({ ok: true, fileName: saved.fileName });
}
