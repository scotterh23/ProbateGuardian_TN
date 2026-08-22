import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { canPostUpdate, getEstateAccess, getSession } from "@/lib/auth";
import { saveUpload } from "@/lib/files";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed || !access.role || !canPostUpdate(access.role)) {
    return NextResponse.json({ error: "You can view this estate, but posting updates is limited to the executor, attorney, and Probate Guardians." }, { status: 403 });
  }

  const form = await req.formData();
  const body = String(form.get("body") || "").trim();
  if (body.length < 2) {
    return NextResponse.json({ error: "Please write a short update." }, { status: 400 });
  }

  const file = form.get("file");
  let fileMeta: { fileName?: string; filePath?: string; fileMime?: string } = {};
  if (file instanceof File && file.size > 0) {
    if (file.size > 12 * 1024 * 1024) {
      return NextResponse.json({ error: "Files must be 12MB or smaller." }, { status: 400 });
    }
    const saved = await saveUpload(file);
    fileMeta = { fileName: saved.fileName, filePath: saved.storedName, fileMime: saved.mime };
  }

  const update = await prisma.estateUpdate.create({
    data: {
      estateId: id,
      authorId: session.id,
      body,
      ...fileMeta,
    },
  });
  await prisma.estate.update({ where: { id }, data: { updatedAt: new Date() } });
  return NextResponse.json({ update });
}
