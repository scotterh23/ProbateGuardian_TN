import Link from "next/link";
import { prisma } from "@/lib/db";
import { BrandLogo } from "@/components/BrandLogo";
import { InviteAcceptForm } from "./InviteAcceptForm";

export default async function InvitePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const invite = await prisma.invite.findUnique({
    where: { token },
    include: {
      estate: { select: { id: true, nickname: true, address: true, city: true, county: true } },
    },
  });

  return (
    <div className="min-h-screen bg-cream px-4 py-12">
      <div className="mx-auto mb-6 flex max-w-md justify-center">
        <BrandLogo href={null} size="hero" />
      </div>
      {!invite ? (
        <InviteMessage
          title="This invite is not valid"
          body="The link may be mistyped. Ask Probate Guardians to send a new invite."
        />
      ) : invite.usedAt ? (
        <InviteMessage
          title="This invite was already used"
          body="If you already created your access, sign in to open the estate."
          href={`/login?next=${encodeURIComponent(`/estates/${invite.estateId}`)}`}
          action="Sign in"
        />
      ) : invite.expiresAt < new Date() ? (
        <InviteMessage
          title="This invite has expired"
          body="Ask Probate Guardians to send a fresh link. Invites are good for 14 days."
        />
      ) : (
        <InviteAcceptForm
          token={token}
          email={invite.email}
          role={invite.role}
          estate={invite.estate}
        />
      )}
    </div>
  );
}

function InviteMessage({
  title,
  body,
  href,
  action,
}: {
  title: string;
  body: string;
  href?: string;
  action?: string;
}) {
  return (
    <div className="mx-auto max-w-md card p-6">
      <h1 className="font-serif text-2xl text-forest">{title}</h1>
      <p className="mt-2 text-muted">{body}</p>
      {href && action ? (
        <Link href={href} className="btn-primary mt-6 inline-flex rounded-xl px-4 py-3">
          {action}
        </Link>
      ) : (
        <Link href="/login" className="mt-6 inline-block text-sm font-semibold text-forest-600">
          Go to sign in
        </Link>
      )}
    </div>
  );
}
