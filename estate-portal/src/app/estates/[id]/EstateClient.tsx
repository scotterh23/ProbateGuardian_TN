"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { EstateProgress, EstateStatus, UserRole } from "@prisma/client";
import { DOC_LABEL, PROGRESS_LABEL, ROLE_LABEL, STATUS_LABEL } from "@/lib/status";

type Comment = {
  id: string;
  body: string;
  createdAt: string;
  author: { name: string; role: UserRole };
};

type Update = {
  id: string;
  body: string;
  createdAt: string;
  fileName?: string | null;
  author: { name: string; role: UserRole };
  comments: Comment[];
};

type Doc = {
  id: string;
  fileName: string;
  category: string;
  createdAt: string;
  uploadedBy: { name: string };
};

export function PostUpdateForm({ estateId }: { estateId: string }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const res = await fetch(`/api/estates/${estateId}/updates`, {
      method: "POST",
      credentials: "same-origin",
      body: new FormData(e.currentTarget),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not post update.");
      return;
    }
    (e.target as HTMLFormElement).reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <label className="block text-sm font-semibold" htmlFor="body">
        New update
      </label>
      <textarea
        id="body"
        name="body"
        required
        rows={4}
        placeholder="What happened this week? Keep it plain so the whole family can follow."
        className="w-full rounded-xl border border-line px-3 py-3"
      />
      <input name="file" type="file" className="block text-sm text-muted" />
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button className="rounded-xl bg-forest px-4 py-2.5 font-semibold text-white" disabled={pending}>
        {pending ? "Posting…" : "Post update"}
      </button>
    </form>
  );
}

export function CommentForm({ updateId }: { updateId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const form = e.currentTarget;
    const body = String(new FormData(form).get("body") || "");
    const res = await fetch(`/api/updates/${updateId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ body }),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not post this note.");
      return;
    }
    form.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="mt-3 flex flex-col gap-2">
      <div className="flex gap-2">
        <input
          name="body"
          required
          placeholder="Add a note for the family"
          className="flex-1 rounded-xl border border-line px-3 py-2 text-sm"
        />
        <button className="rounded-xl border border-line px-3 py-2 text-sm font-semibold" disabled={pending}>
          Reply
        </button>
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
    </form>
  );
}

export function UpdatesList({
  updates,
  canReply,
}: {
  updates: Update[];
  canReply: boolean;
}) {
  if (updates.length === 0) {
    return <p className="text-muted">No updates yet. The first note will appear here.</p>;
  }
  return (
    <ol className="space-y-6">
      {updates.map((update) => (
        <li key={update.id} className="border-b border-line pb-6 last:border-0">
          <p className="text-sm text-muted">
            {update.author.name} · {ROLE_LABEL[update.author.role]} ·{" "}
            {new Date(update.createdAt).toLocaleString()}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-forest">{update.body}</p>
          {update.fileName && (
            <a className="mt-2 inline-block text-sm font-semibold text-accent" href={`/api/files/${update.id}`}>
              Attachment: {update.fileName}
            </a>
          )}
          {update.comments.length > 0 && (
            <ul className="mt-3 space-y-2 rounded-xl bg-mist p-3">
              {update.comments.map((c) => (
                <li key={c.id} className="text-sm">
                  <span className="font-semibold">{c.author.name}</span>{" "}
                  <span className="text-muted">· {ROLE_LABEL[c.author.role]}</span>
                  <p>{c.body}</p>
                </li>
              ))}
            </ul>
          )}
          {canReply && <CommentForm updateId={update.id} />}
        </li>
      ))}
    </ol>
  );
}

export function DocumentUpload({ estateId }: { estateId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const form = e.currentTarget;
    const res = await fetch(`/api/estates/${estateId}/documents`, {
      method: "POST",
      credentials: "same-origin",
      body: new FormData(form),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not upload that file.");
      return;
    }
    form.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3">
      <label className="text-sm">
        Category
        <select name="category" className="mt-1 w-full rounded-xl border border-line px-3 py-2">
          {Object.entries(DOC_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <input name="file" type="file" required className="w-full text-sm" />
      <div>
        <button className="rounded-xl bg-forest px-4 py-2.5 font-semibold text-white" disabled={pending}>
          {pending ? "Uploading…" : "Upload"}
        </button>
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
    </form>
  );
}

export function DocumentList({
  documents,
  canDelete,
}: {
  documents: Doc[];
  canDelete?: boolean;
}) {
  const router = useRouter();
  const [pendingId, setPendingId] = useState("");
  const [error, setError] = useState("");

  async function remove(doc: Doc) {
    if (!confirm(`Delete “${doc.fileName}” from the vault? This cannot be undone.`)) return;
    setError("");
    setPendingId(doc.id);
    const res = await fetch(`/api/documents/${doc.id}`, {
      method: "DELETE",
      credentials: "same-origin",
    });
    const data = await res.json().catch(() => ({}));
    setPendingId("");
    if (!res.ok) {
      setError(data.error || "Could not delete that file.");
      return;
    }
    router.refresh();
  }

  if (documents.length === 0) {
    return <p className="mt-3 text-muted">The vault is empty.</p>;
  }
  return (
    <>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      <ul className="mt-4 divide-y divide-line">
        {documents.map((doc) => (
          <li key={doc.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
            <div>
              <a className="font-semibold text-forest underline-offset-2 hover:underline" href={`/api/documents/${doc.id}`}>
                {doc.fileName}
              </a>
              <p className="text-sm text-muted">
                {DOC_LABEL[doc.category] || doc.category} · {doc.uploadedBy.name}
              </p>
            </div>
            {canDelete && (
              <button
                type="button"
                className="text-sm font-semibold text-red-800 hover:underline disabled:opacity-60"
                disabled={pendingId === doc.id}
                onClick={() => remove(doc)}
              >
                {pendingId === doc.id ? "Deleting…" : "Delete"}
              </button>
            )}
          </li>
        ))}
      </ul>
    </>
  );
}

export function StatusEditor({
  estateId,
  status,
}: {
  estateId: string;
  status: EstateStatus;
}) {
  const router = useRouter();
  async function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    await fetch(`/api/estates/${estateId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: e.target.value }),
    });
    router.refresh();
  }
  return (
    <label className="text-sm">
      <span className="mb-1 block font-semibold">Update house status</span>
      <select
        defaultValue={status}
        onChange={onChange}
        className="rounded-xl border border-line bg-white px-3 py-2"
      >
        {Object.entries(STATUS_LABEL).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function ProgressEditor({
  estateId,
  progress,
}: {
  estateId: string;
  progress: EstateProgress;
}) {
  const router = useRouter();
  async function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    await fetch(`/api/estates/${estateId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ progress: e.target.value }),
    });
    router.refresh();
  }
  return (
    <label className="text-sm">
      <span className="mb-1 block font-semibold">Update estate stage</span>
      <select
        defaultValue={progress}
        onChange={onChange}
        className="w-full rounded-xl border border-line bg-white px-3 py-2"
      >
        {Object.entries(PROGRESS_LABEL).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function InviteForm({ estateId }: { estateId: string }) {
  const [created, setCreated] = useState<{ url: string; email: string; token: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [emailNote, setEmailNote] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setCopied(false);
    setEmailNote("");
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email") || "");
    const res = await fetch("/api/invites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        estateId,
        email,
        role: form.get("role"),
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "Could not create invite.");
      return;
    }
    const token = String(data.invitePath || data.inviteUrl || "").split("/").pop() || "";
    const path = data.invitePath || `/invite/${token}`;
    const origin = window.location.origin;
    setCreated({
      url: `${origin}${path.startsWith("/") ? path : `/${path}`}`,
      email,
      token,
    });
    (e.target as HTMLFormElement).reset();
  }

  async function copyLink() {
    if (!created) return;
    try {
      await navigator.clipboard.writeText(created.url);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  async function sendEmail() {
    if (!created?.token) return;
    setEmailNote("Sending…");
    const res = await fetch(`/api/invites/${created.token}/send-email`, {
      method: "POST",
      credentials: "same-origin",
    });
    const data = await res.json().catch(() => ({}));
    setEmailNote(data.message || (res.ok ? `Email sent to ${created.email}.` : "Could not send email."));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <p className="text-sm text-muted">
        Create a link for an Executor, Heir, or Attorney. They set a password and land in this
        estate.
      </p>
      <input
        name="email"
        type="email"
        required
        placeholder="email@example.com"
        className="w-full rounded-xl border border-line px-3 py-2"
      />
      <select name="role" className="w-full rounded-xl border border-line px-3 py-2">
        <option value="EXECUTOR">Executor / Administrator</option>
        <option value="HEIR">Heir</option>
        <option value="ATTORNEY">Attorney / paralegal</option>
      </select>
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button className="rounded-xl bg-forest px-4 py-2.5 font-semibold text-white">Create invite link</button>
      {created && (
        <div className="space-y-2 rounded-xl bg-mist p-3 text-sm">
          <p className="font-semibold text-forest">Invite ready for {created.email}</p>
          <input
            readOnly
            value={created.url}
            className="w-full rounded-lg border border-line bg-white px-2 py-2 text-xs"
          />
          <div className="flex flex-wrap gap-2">
            <button type="button" className="rounded-xl bg-forest px-3 py-2 font-semibold text-white" onClick={copyLink}>
              {copied ? "Copied" : "Copy link"}
            </button>
            <button type="button" className="rounded-xl border border-line px-3 py-2 font-semibold" onClick={sendEmail}>
              Send email
            </button>
          </div>
          {emailNote && <p className="text-muted">{emailNote}</p>}
        </div>
      )}
    </form>
  );
}

export function DeleteEstateForm({
  estateId,
  nickname,
}: {
  estateId: string;
  nickname: string;
}) {
  const [confirmName, setConfirmName] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    if (confirmName.trim() !== nickname) {
      setError(`Type ${nickname} exactly to confirm.`);
      return;
    }
    if (!confirm(`Permanently delete “${nickname}” and all of its documents, updates, and invites?`)) {
      return;
    }
    setPending(true);
    const res = await fetch(`/api/estates/${estateId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ confirm: nickname }),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not delete this estate.");
      return;
    }
    window.location.href = "/admin";
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <p className="text-sm text-muted">
        This removes the estate, vault files, activity, questions, and unused invites. Type{" "}
        <span className="font-semibold text-forest">{nickname}</span> to confirm.
      </p>
      <input
        value={confirmName}
        onChange={(e) => setConfirmName(e.target.value)}
        placeholder={nickname}
        className="w-full rounded-xl border border-line px-3 py-2"
      />
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button
        className="rounded-xl bg-red-800 px-4 py-2.5 font-semibold text-white disabled:opacity-60"
        disabled={pending || confirmName.trim() !== nickname}
      >
        {pending ? "Deleting…" : "Delete estate"}
      </button>
    </form>
  );
}

type Question = {
  id: string;
  body: string;
  createdAt: string;
  author: { name: string };
};

export function QuestionForm({ estateId }: { estateId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const form = e.currentTarget;
    const body = String(new FormData(form).get("body") || "");
    const res = await fetch(`/api/estates/${estateId}/questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ body }),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not send that question.");
      return;
    }
    form.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <textarea
        name="body"
        required
        minLength={4}
        rows={4}
        placeholder="Ask Probate Guardians a question about the house, timeline, or next steps."
        className="w-full rounded-xl border border-line px-3 py-3"
      />
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button className="rounded-xl bg-forest px-4 py-2.5 font-semibold text-white" disabled={pending}>
        {pending ? "Sending…" : "Send to Probate Guardians"}
      </button>
    </form>
  );
}

export function QuestionList({
  questions,
  empty,
}: {
  questions: Question[];
  empty: string;
}) {
  if (questions.length === 0) {
    return <p className="mt-3 text-sm text-muted">{empty}</p>;
  }
  return (
    <ul className="mt-4 space-y-3">
      {questions.map((q) => (
        <li key={q.id} className="rounded-xl bg-mist p-3 text-sm">
          <p className="text-muted">
            {q.author.name} · {new Date(q.createdAt).toLocaleString()}
          </p>
          <p className="mt-1 whitespace-pre-wrap text-forest">{q.body}</p>
        </li>
      ))}
    </ul>
  );
}
