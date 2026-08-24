import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { canManageVendors, getSession } from "@/lib/auth";

const vendorSchema = z.object({
  category: z
    .enum([
      "ESTATE_SALE",
      "CLEAN_OUT",
      "LAWN",
      "LOCKSMITH",
      "CLEANING",
      "HANDYMAN",
      "APPRAISER",
      "CASH_ADVANCE",
    ])
    .optional(),
  name: z.string().min(2).max(120).optional(),
  description: z.string().min(8).max(400).optional(),
  phone: z.string().max(40).optional().nullable(),
  email: z.string().email().optional().nullable().or(z.literal("")),
  serviceArea: z.string().max(160).optional().nullable(),
  notes: z.string().max(400).optional().nullable(),
});

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session || !canManageVendors(session.role)) {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const { id } = await params;
  const parsed = vendorSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid vendor update." }, { status: 400 });
  }
  const data = {
    ...parsed.data,
    phone: parsed.data.phone || null,
    email: parsed.data.email || null,
    serviceArea: parsed.data.serviceArea || null,
    notes: parsed.data.notes || null,
  };
  const vendor = await prisma.vendor.update({ where: { id }, data });
  return NextResponse.json({ vendor });
}

export async function DELETE(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session || !canManageVendors(session.role)) {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const { id } = await params;
  await prisma.vendor.delete({ where: { id } });
  return NextResponse.json({ ok: true });
}
