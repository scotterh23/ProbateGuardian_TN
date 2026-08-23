import { NextRequest, NextResponse } from "next/server";

function isInvitePath(pathname: string) {
  return pathname === "/invite" || pathname.startsWith("/invite/");
}

function isPublic(pathname: string) {
  if (isInvitePath(pathname)) return true;
  if (pathname === "/login") return true;
  if (pathname.startsWith("/api/auth/login")) return true;
  if (pathname.startsWith("/api/auth/logout")) return true;
  if (pathname.startsWith("/api/auth/accept-invite")) return true;
  return false;
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.startsWith("/images/") ||
    pathname.startsWith("/api/")
  ) {
    return NextResponse.next();
  }

  if (isInvitePath(pathname)) {
    return NextResponse.next();
  }

  // If auth middleware previously bounced an invite to /login?next=/invite/...,
  // send them back to the invite form instead of showing login.
  if (pathname === "/login") {
    const next = req.nextUrl.searchParams.get("next") || "";
    if (/^\/invite\/[a-zA-Z0-9_-]+$/.test(next)) {
      const invite = req.nextUrl.clone();
      invite.pathname = next;
      invite.search = "";
      return NextResponse.redirect(invite);
    }
    return NextResponse.next();
  }

  if (isPublic(pathname)) return NextResponse.next();

  const token = req.cookies.get("pg_portal_session")?.value;
  if (!token) {
    const login = new URL("/login", req.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  const parts = token.split(".");
  if (parts.length !== 3) {
    const login = new URL("/login", req.url);
    return NextResponse.redirect(login);
  }
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
    if (!payload?.id || (payload.exp && payload.exp * 1000 < Date.now())) {
      throw new Error("expired");
    }
    return NextResponse.next();
  } catch {
    const login = new URL("/login", req.url);
    return NextResponse.redirect(login);
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|api/|images/|invite/).*)"],
};
