"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { EstateStatus, UserRole } from "@prisma/client";
import { DOC_LABEL, ROLE_LABEL, STATUS_LABEL } from "@/lib/status";

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

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    const form = e.currentTarget;
    const body = String(new FormData(form).get("body") || "");
    await fetch(`/api/updates/${updateId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body }),
    });
    setPending(false);
    form.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="mt-3 flex gap-2">
      <input
        name="body"
        required
        placeholder="Add a comment"
        className="flex-1 rounded-xl border border-line px-3 py-2 text-sm"
      />
      <button className="rounded-xl border border-line px-3 py-2 text-sm font-semibold" disabled={pending}>
        Reply
      </button>
    </form>
  );
}

export function UpdatesList({ updates }: { updates: Update[] }) {
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
          <CommentForm updateId={update.id} />
        </li>
      ))}
    </ol>
  );
}

export function DocumentUpload({ estateId }: { estateId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    await fetch(`/api/estates/${estateId}/documents`, {
      method: "POST",
      body: new FormData(e.currentTarget),
    });
    setPending(false);
    (e.target as HTMLFormElement).reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
      <label className="flex-1 text-sm">
        Category
        <select name="category" className="mt-1 w-full rounded-xl border border-line px-3 py-2">
          {Object.entries(DOC_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <input name="file" type="file" required className="flex-1 text-sm" />
      <button className="rounded-xl bg-forest px-4 py-2.5 font-semibold text-white" disabled={pending}>
        {pending ? "Uploading…" : "Upload"}
      </button>
    </form>
  );
}

export function DocumentList({ documents }: { documents: Doc[] }) {
  if (documents.length === 0) {
    return <p className="mt-3 text-muted">The vault is empty.</p>;
  }
  return (
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
        </li>
      ))}
    </ul>
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
      <span className="mb-1 block font-semibold">Update status</span>
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

export function InviteForm({ estateId }: { estateId: string }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setUrl("");
    const form = new FormData(e.currentTarget);
    const res = await fetch("/api/invites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        estateId,
        email: form.get("email"),
        role: form.get("role"),
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "Could not create invite.");
      return;
    }
    setUrl(data.inviteUrl);
    (e.target as HTMLFormElement).reset();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <p className="text-sm text-muted">
        Phase 1 sends a copyable invite link (email delivery can be added later). Share it with the
        executor, heir, or attorney.
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
        <option value="HEIR">Heir / family member</option>
        <option value="ATTORNEY">Attorney / paralegal</option>
      </select>
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button className="rounded-xl bg-forest px-4 py-2.5 font-semibold text-white">Create invite link</button>
      {url && (
        <p className="break-all rounded-xl bg-mist p-3 text-sm">
          Invite link: {url}
        </p>
      )}
    </form>
  );
}
