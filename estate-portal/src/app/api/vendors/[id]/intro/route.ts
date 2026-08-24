import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getEstateAccess, getSession } from "@/lib/auth";
import { sendVendorIntroEmail } from "@/lib/vendor-email";
import { ROLE_LABEL, VENDOR_CATEGORY_LABEL } from "@/lib/status";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { id } = await params;
  const body = await req.json().catch(() => ({}));
  const estateId = String(body.estateId || "");
  if (!estateId) return NextResponse.json({ error: "Estate is required." }, { status: 400 });

  const access = await getEstateAccess(session, estateId);
  if (!access.allowed || !access.role) {
    return NextResponse.json({ error: "Not found." }, { status: 404 });
  }

  const [vendor, estate] = await Promise.all([
    prisma.vendor.findUnique({ where: { id } }),
    prisma.estate.findUnique({ where: { id: estateId } }),
  ]);
  if (!vendor || !estate) return NextResponse.json({ error: "Not found." }, { status: 404 });

  const result = await sendVendorIntroEmail({
    vendorName: vendor.name,
    vendorCategory: VENDOR_CATEGORY_LABEL[vendor.category],
    requesterName: session.name,
    requesterEmail: session.email,
    requesterRole: ROLE_LABEL[access.role],
    estateName: estate.nickname,
    estateAddress: `${estate.address}, ${estate.city}`,
  });

  if (!result.sent) {
    return NextResponse.json(
      {
        sent: false,
        message:
          result.reason === "missing_api_key"
            ? "Email is not configured. Call or email the vendor directly, or ask Probate Guardians for an introduction."
            : "Could not send the introduction request. Contact Probate Guardians directly.",
      },
      { status: 500 },
    );
  }

  return NextResponse.json({
    sent: true,
    message: `We notified Probate Guardians. They’ll introduce you to ${vendor.name}.`,
  });
}
