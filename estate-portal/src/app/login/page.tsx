import { redirect } from "next/navigation";
import { LoginScreen } from "./LoginScreen";

export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  if (next && /^\/invite\/[a-zA-Z0-9_-]+$/.test(next)) {
    redirect(next);
  }
  return <LoginScreen />;
}
