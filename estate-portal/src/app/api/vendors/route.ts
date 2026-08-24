import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { canManageVendors, getSession } from "@/lib/auth";

const vendorSchema = z.object({
  category: z.enum([
    "ESTATE_SALE",
    "CLEAN_OUT",
    "LAWN",
    "LOCKSMITH",
    "CLEANING",
    "HANDYMAN",
    "APPRAISER",
    "CASH_ADVANCE",
    "OTHER",
  ]),
  name: z.string().min(2).max(120),
  description: z.string().min(8).max(400),
  phone: z.string().max(40).optional().nullable(),
  email: z.string().email().optional().nullable().or(z.literal("")),
  serviceArea: z.string().max(160).optional().nullable(),
  notes: z.string().max(400).optional().nullable(),
});

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const vendors = await prisma.vendor.findMany({ orderBy: [{ category: "asc" }, { sortOrder: "asc" }, { name: "asc" }] });
  return NextResponse.json({ vendors });
}

export async function POST(req: Request) {
  const session = await getSession();
  if (!session || !canManageVendors(session.role)) {
    return NextResponse.json({ error: "Admin only." }, { status: 403 });
  }
  const parsed = vendorSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "Name, category, and a short description are required." }, { status: 400 });
  }
  const data = {
    ...parsed.data,
    phone: parsed.data.phone || null,
    email: parsed.data.email || null,
    serviceArea: parsed.data.serviceArea || null,
    notes: parsed.data.notes || null,
  };
  const vendor = await prisma.vendor.create({ data });
  return NextResponse.json({ vendor });
}
