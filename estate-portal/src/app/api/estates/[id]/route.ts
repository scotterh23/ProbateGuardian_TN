import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { canUpdateProgress, canUpdateSnapshot, getEstateAccess, getSession } from "@/lib/auth";
import { removeUpload } from "@/lib/files";

const patchSchema = z.object({
  nickname: z.string().min(2).optional(),
  address: z.string().min(3).optional(),
  city: z.string().min(2).optional(),
  county: z.string().min(2).optional(),
  status: z.enum(["LETTERS", "VALUATION", "LISTED", "UNDER_CONTRACT", "CLOSED"]).optional(),
  progress: z
    .enum([
      "LETTERS_ISSUED",
      "INVENTORY_FILED",
      "NOTICE_TO_CREDITORS",
      "CREDITOR_PERIOD_ENDED",
      "DEBTS_TAXES_SETTLED",
      "FINAL_ACCOUNTING",
      "ESTATE_CLOSED",
    ])
    .optional(),
  estimatedValue: z.number().int().nonnegative().nullable().optional(),
  listPrice: z.number().int().nonnegative().nullable().optional(),
  listingNotes: z.string().max(500).nullable().optional(),
  contractPrice: z.number().int().nonnegative().nullable().optional(),
  transactionStatus: z
    .enum(["INSPECTION", "APPRAISAL", "FINANCING", "CLEAR_TO_CLOSE"])
    .nullable()
    .optional(),
  salePrice: z.number().int().nonnegative().nullable().optional(),
  netToEstate: z.number().int().nonnegative().nullable().optional(),
  netNotes: z.string().max(500).nullable().optional(),
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
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed || !access.role) {
    return NextResponse.json({ error: "Not found." }, { status: 404 });
  }
  const parsed = patchSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid estate update." }, { status: 400 });
  }
  const {
    progress,
    estimatedValue,
    listPrice,
    listingNotes,
    contractPrice,
    transactionStatus,
    salePrice,
    netToEstate,
    netNotes,
    ...adminRest
  } = parsed.data;
  const adminFields = Object.fromEntries(
    Object.entries(adminRest).filter(([, value]) => value !== undefined),
  );
  const snapshotFields = Object.fromEntries(
    Object.entries({
      estimatedValue,
      listPrice,
      listingNotes,
      contractPrice,
      transactionStatus,
      salePrice,
      netToEstate,
      netNotes,
    }).filter(([, value]) => value !== undefined),
  );
  if (Object.keys(adminFields).length > 0 && session.role !== "ADMIN") {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  if (progress && !canUpdateProgress(access.role)) {
    return NextResponse.json({ error: "Only the executor and Probate Guardians can update estate progress." }, { status: 403 });
  }
  if (Object.keys(snapshotFields).length > 0 && !canUpdateSnapshot(access.role)) {
    return NextResponse.json({ error: "Only the executor and Probate Guardians can update the property snapshot." }, { status: 403 });
  }
  const estate = await prisma.estate.update({
    where: { id },
    data: {
      ...adminFields,
      ...snapshotFields,
      ...(progress ? { progress } : {}),
    },
  });
  return NextResponse.json({ estate });
}

export async function DELETE(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session || session.role !== "ADMIN") {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const { id } = await params;
  const body = await req.json().catch(() => ({}));
  const estate = await prisma.estate.findUnique({
    where: { id },
    include: { documents: { select: { filePath: true } } },
  });
  if (!estate) return NextResponse.json({ error: "Not found." }, { status: 404 });
  const confirm = String(body.confirm || "").trim();
  if (confirm !== estate.nickname) {
    return NextResponse.json(
      { error: `Type the estate name “${estate.nickname}” to confirm deletion.` },
      { status: 400 },
    );
  }
  await Promise.all(estate.documents.map((doc) => removeUpload(doc.filePath)));
  await prisma.estate.delete({ where: { id } });
  return NextResponse.json({ ok: true });
}
