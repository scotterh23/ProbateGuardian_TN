import { notFound, redirect } from "next/navigation";
import {
  canAskQuestion,
  canComment,
  canManageEstate,
  canPostUpdate,
  canUploadDocs,
  canViewAllQuestions,
  getEstateAccess,
  getSession,
} from "@/lib/auth";
import { prisma } from "@/lib/db";
import { Shell } from "@/components/Shell";
import { StatusBadge } from "@/components/StatusBadge";
import { Timeline } from "@/components/Timeline";
import { ROLE_LABEL } from "@/lib/status";
import {
  DocumentList,
  DocumentUpload,
  InviteForm,
  PostUpdateForm,
  QuestionForm,
  QuestionList,
  StatusEditor,
  UpdatesList,
} from "./EstateClient";

export default async function EstatePage({ params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) redirect("/login");
  const { id } = await params;
  const access = await getEstateAccess(session, id);
  if (!access.allowed || !access.role) notFound();

  const estate = await prisma.estate.findUnique({
    where: { id },
    include: {
      members: { include: { user: { select: { name: true, email: true, role: true } } } },
      updates: {
        orderBy: { createdAt: "desc" },
        include: {
          author: { select: { name: true, role: true } },
          comments: {
            orderBy: { createdAt: "asc" },
            include: { author: { select: { name: true, role: true } } },
          },
        },
      },
      documents: {
        orderBy: { createdAt: "desc" },
        include: { uploadedBy: { select: { name: true } } },
      },
      questions: {
        orderBy: { createdAt: "desc" },
        include: { author: { select: { id: true, name: true, role: true } } },
      },
    },
  });
  if (!estate) notFound();

  const role = access.role;
  const attorneyView = role === "ATTORNEY";
  const questions = canViewAllQuestions(role)
    ? estate.questions
    : canAskQuestion(role)
      ? estate.questions.filter((q) => q.authorId === session.id)
      : [];
  const visibleUpdates = estate.updates.map((u) => ({
    ...u,
    createdAt: u.createdAt.toISOString(),
    comments: u.comments
      .filter((c) => role !== "HEIR" || c.author.role !== "HEIR")
      .map((c) => ({ ...c, createdAt: c.createdAt.toISOString() })),
  }));

  return (
    <Shell user={session}>
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-muted">
          {estate.county} County · {attorneyView ? "Attorney view" : ROLE_LABEL[role]}
        </p>
        <div className="mt-1 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="font-serif text-3xl text-forest">{estate.nickname}</h1>
            <p className="text-lg text-muted">
              {estate.address}, {estate.city}
            </p>
          </div>
          <StatusBadge status={estate.status} />
        </div>
      </div>

      <section className="card mb-6 p-5">
        <h2 className="mb-4 font-serif text-xl">Where things stand</h2>
        <Timeline status={estate.status} />
        {canManageEstate(role) && (
          <div className="mt-5 border-t border-line pt-4">
            <StatusEditor estateId={estate.id} status={estate.status} />
          </div>
        )}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
        <section className="card p-5">
          <h2 className="mb-4 font-serif text-xl">Activity</h2>
          {canPostUpdate(role) && (
            <div className="mb-8 rounded-xl bg-mist p-4">
              <PostUpdateForm estateId={estate.id} />
            </div>
          )}
          {role === "HEIR" && (
            <p className="mb-4 text-sm text-muted">
              You can read every update and document. Questions for Probate Guardians stay with the
              team — they are not posted for other family members to see.
            </p>
          )}
          <UpdatesList updates={visibleUpdates} canReply={canComment(role)} />
        </section>

        <div className="space-y-6">
          <section className="card p-5">
            <h2 className="font-serif text-xl">People on this estate</h2>
            <ul className="mt-3 space-y-2">
              {estate.members.map((m) => (
                <li key={m.id} className="text-sm">
                  <span className="font-semibold">{m.user.name}</span>
                  <span className="text-muted"> · {ROLE_LABEL[m.role]}</span>
                </li>
              ))}
            </ul>
            {canManageEstate(role) && (
              <div className="mt-5 border-t border-line pt-4">
                <h3 className="mb-2 font-semibold">Invite someone</h3>
                <InviteForm estateId={estate.id} />
              </div>
            )}
          </section>

          {(canAskQuestion(role) || canViewAllQuestions(role)) && (
            <section className="card p-5">
              <h2 className="font-serif text-xl">
                {canViewAllQuestions(role) ? "Family questions" : "Ask Probate Guardians"}
              </h2>
              <p className="mt-1 text-sm text-muted">
                {canViewAllQuestions(role)
                  ? "Heirs can send questions here. Other family members do not see them."
                  : "Only the Probate Guardians team can see what you send. Other heirs cannot."}
              </p>
              {canAskQuestion(role) && (
                <div className="mt-4">
                  <QuestionForm estateId={estate.id} />
                </div>
              )}
              <QuestionList
                questions={questions.map((q) => ({
                  id: q.id,
                  body: q.body,
                  createdAt: q.createdAt.toISOString(),
                  author: { name: q.author.name },
                }))}
                empty={
                  canViewAllQuestions(role)
                    ? "No questions yet."
                    : "Your questions to the team will appear here."
                }
              />
            </section>
          )}

          <section className="card p-5">
            <h2 className="font-serif text-xl">Document vault</h2>
            <p className="mt-1 text-sm text-muted">
              Wills, Letters, appraisals, photos, and contracts — in one place.
            </p>
            {canUploadDocs(role) && <DocumentUpload estateId={estate.id} />}
            <DocumentList
              documents={estate.documents.map((d) => ({
                ...d,
                createdAt: d.createdAt.toISOString(),
              }))}
            />
          </section>
        </div>
      </div>
    </Shell>
  );
}
