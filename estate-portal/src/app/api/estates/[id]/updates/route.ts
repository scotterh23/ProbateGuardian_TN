import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { canPostUpdate, getEstateAccess, getSession } from "@/lib/auth";
import { getUploadedFile, MAX_UPLOAD_BYTES, saveUpload } from "@/lib/files";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed || !access.role || !canPostUpdate(access.role)) {
    return NextResponse.json({ error: "You can view this estate, but posting updates is limited to the executor, attorney, and Probate Guardians." }, { status: 403 });
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return NextResponse.json({ error: "Could not read the upload. Try a smaller file." }, { status: 400 });
  }
  const body = String(form.get("body") || "").trim();
  if (body.length < 2) {
    return NextResponse.json({ error: "Please write a short update." }, { status: 400 });
  }

  const file = getUploadedFile(form);
  let fileMeta: { fileName?: string; filePath?: string; fileMime?: string } = {};
  if (file) {
    if (file.size > MAX_UPLOAD_BYTES) {
      return NextResponse.json({ error: "Files must be 12MB or smaller." }, { status: 400 });
    }
    try {
      const saved = await saveUpload(file);
      fileMeta = { fileName: saved.fileName, filePath: saved.storedName, fileMime: saved.mime };
    } catch (error) {
      const message = error instanceof Error ? error.message : "";
      const needsBlob =
        process.env.VERCEL === "1" || /blob|token|oidc|store/i.test(message);
      return NextResponse.json(
        {
          error: needsBlob
            ? "File storage is not configured. Create a Private Vercel Blob store and connect it to this Vercel project."
            : "Could not attach that file.",
        },
        { status: 500 },
      );
    }
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
