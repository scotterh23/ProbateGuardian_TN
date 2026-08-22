import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { canUploadDocs, getEstateAccess, getSession } from "@/lib/auth";
import { saveUpload } from "@/lib/files";

const CATEGORIES = ["WILL", "LETTERS", "APPRAISAL", "PHOTOS", "CONTRACTS", "OTHER"] as const;

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed || !access.role || !canUploadDocs(access.role)) {
    return NextResponse.json({ error: "Uploading is limited to the executor, attorney, and Probate Guardians." }, { status: 403 });
  }

  const form = await req.formData();
  const file = form.get("file");
  const categoryRaw = String(form.get("category") || "OTHER");
  const category = CATEGORIES.includes(categoryRaw as (typeof CATEGORIES)[number])
    ? categoryRaw
    : "OTHER";

  if (!(file instanceof File) || file.size === 0) {
    return NextResponse.json({ error: "Choose a file to upload." }, { status: 400 });
  }
  if (file.size > 12 * 1024 * 1024) {
    return NextResponse.json({ error: "Files must be 12MB or smaller." }, { status: 400 });
  }

  const saved = await saveUpload(file);
  const doc = await prisma.document.create({
    data: {
      estateId: id,
      uploadedById: session.id,
      category: category as "WILL" | "LETTERS" | "APPRAISAL" | "PHOTOS" | "CONTRACTS" | "OTHER",
      fileName: saved.fileName,
      filePath: saved.storedName,
      fileMime: saved.mime,
      fileSize: saved.size,
    },
  });
  return NextResponse.json({ document: doc });
}
