import { NextRequest, NextResponse } from "next/server";

const PUBLIC = ["/login", "/invite", "/api/auth/login", "/api/auth/logout"];

function isPublic(pathname: string) {
  if (pathname.startsWith("/invite/")) return true;
  if (pathname.startsWith("/api/auth/accept-invite")) return true;
  return PUBLIC.includes(pathname);
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
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
  matcher: ["/((?!_next/static|_next/image|api/|images/).*)"],
};
