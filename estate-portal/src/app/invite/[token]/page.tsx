import { InviteClient } from "./InviteClient";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export default async function InvitePage({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { token } = await params;
  const { error } = await searchParams;
  return <InviteClient token={token} error={error} />;
}
