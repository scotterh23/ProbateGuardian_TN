import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { UserRole } from "@prisma/client";
import { prisma } from "./db";

const COOKIE = "pg_portal_session";

export type SessionUser = {
  id: string;
  email: string;
  name: string;
  role: UserRole;
};

function secret() {
  const value = process.env.AUTH_SECRET;
  if (!value || value.length < 16) {
    throw new Error("AUTH_SECRET must be set (16+ characters).");
  }
  return new TextEncoder().encode(value);
}

export async function createSession(user: SessionUser) {
  const token = await new SignJWT({
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(user.id)
    .setIssuedAt()
    .setExpirationTime("30d")
    .sign(secret());

  const store = await cookies();
  store.set(COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
}

export async function clearSession() {
  const store = await cookies();
  store.delete(COOKIE);
}

export async function getSession(): Promise<SessionUser | null> {
  const store = await cookies();
  const token = store.get(COOKIE)?.value;
  if (!token) return null;
  try {
    const { payload } = await jwtVerify(token, secret());
    if (!payload.id || !payload.email || !payload.role) return null;
    return {
      id: String(payload.id),
      email: String(payload.email),
      name: String(payload.name || ""),
      role: payload.role as UserRole,
    };
  } catch {
    return null;
  }
}

export async function requireSession() {
  const session = await getSession();
  if (!session) {
    throw new Error("UNAUTHENTICATED");
  }
  return session;
}

export async function userCanAccessEstate(user: SessionUser, estateId: string) {
  if (user.role === "ADMIN") return true;
  const member = await prisma.estateMember.findUnique({
    where: { estateId_userId: { estateId, userId: user.id } },
  });
  return Boolean(member);
}

export async function getEstateAccess(user: SessionUser, estateId: string) {
  if (user.role === "ADMIN") {
    return { allowed: true as const, role: "ADMIN" as UserRole };
  }
  const member = await prisma.estateMember.findUnique({
    where: { estateId_userId: { estateId, userId: user.id } },
  });
  if (!member) return { allowed: false as const, role: null };
  return { allowed: true as const, role: member.role };
}

export function canPostUpdate(role: UserRole) {
  return role === "ADMIN" || role === "EXECUTOR" || role === "ATTORNEY";
}

export function canUploadDocs(role: UserRole) {
  return role === "ADMIN" || role === "EXECUTOR" || role === "ATTORNEY";
}

export function canManageEstate(role: UserRole) {
  return role === "ADMIN";
}

export function canComment(role: UserRole) {
  return Boolean(role);
}
