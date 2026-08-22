import { NextResponse } from "next/server";
import { clearSession } from "@/lib/auth";

export async function POST(req: Request) {
  await clearSession();
  const url = new URL("/login", req.url);
  return NextResponse.redirect(url, { status: 303 });
}
