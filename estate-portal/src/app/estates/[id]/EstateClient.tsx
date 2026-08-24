"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { EstateProgress, EstateStatus, TransactionStatus, UserRole } from "@prisma/client";
import {
  DOC_LABEL,
  formatDollars,
  PROGRESS_LABEL,
  ROLE_LABEL,
  STATUS_LABEL,
  TX_STATUS_LABEL,
  TX_STATUS_ORDER,
} from "@/lib/status";

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

type Snapshot = {
  estimatedValue: number | null;
  listPrice: number | null;
  listingNotes: string | null;
  contractPrice: number | null;
  transactionStatus: TransactionStatus | null;
  salePrice: number | null;
  netToEstate: number | null;
  netNotes: string | null;
  cashOfferRange: string | null;
  cashNet: number | null;
  cashNotes: string | null;
  prepCosts: number | null;
  marketNet: number | null;
  marketNotes: string | null;
  listingUrl: string | null;
  contractUrl: string | null;
  settlementUrl: string | null;
  settlementFileName: string | null;
};

function hrefFor(url: string) {
  const text = url.trim();
  if (!text) return "";
  return /^https?:\/\//i.test(text) ? text : `https://${text}`;
}

function VerifyLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="btn-primary inline-flex rounded-xl px-4 py-2.5 text-sm"
    >
      {label}
    </a>
  );
}

function SnapshotVerify({
  href,
  label,
  emptyHint,
  canEdit,
}: {
  href: string | null;
  label: string;
  emptyHint: string;
  canEdit: boolean;
}) {
  if (href) {
    return (
      <div className="mb-3">
        <VerifyLink href={href} label={label} />
      </div>
    );
  }
  if (canEdit) {
    return <p className="mb-2 text-sm text-muted">{emptyHint}</p>;
  }
  return null;
}

function FieldHint({ children }: { children: string }) {
  return <span className="mt-1 block text-xs text-muted">{children}</span>;
}

function parseDollars(raw: FormDataEntryValue | null) {
  const text = String(raw || "").replace(/[$,\s]/g, "");
  if (!text) return null;
  const n = Number(text);
  return Number.isFinite(n) && n >= 0 ? Math.round(n) : null;
}

export function PropertySnapshot({
  estateId,
  status,
  snapshot,
  canEdit,
}: {
  estateId: string;
  status: EstateStatus;
  snapshot: Snapshot;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const comparePaths = status === "LETTERS" || status === "VALUATION";

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const form = new FormData(e.currentTarget);
    const payload: Record<string, unknown> = {};
    if (comparePaths) {
      payload.cashOfferRange = String(form.get("cashOfferRange") || "").trim() || null;
      payload.cashNet = parseDollars(form.get("cashNet"));
      payload.cashNotes = String(form.get("cashNotes") || "").trim() || null;
      payload.estimatedValue = parseDollars(form.get("estimatedValue"));
      payload.prepCosts = parseDollars(form.get("prepCosts"));
      payload.marketNet = parseDollars(form.get("marketNet"));
      payload.marketNotes = String(form.get("marketNotes") || "").trim() || null;
    }
    if (status === "LISTED") {
      payload.listPrice = parseDollars(form.get("listPrice"));
      payload.listingUrl = String(form.get("listingUrl") || "").trim() || null;
      payload.listingNotes = String(form.get("listingNotes") || "").trim() || null;
    }
    if (status === "UNDER_CONTRACT") {
      payload.contractPrice = parseDollars(form.get("contractPrice"));
      payload.transactionStatus = String(form.get("transactionStatus") || "") || null;
      payload.contractUrl = String(form.get("contractUrl") || "").trim() || null;
    }
    if (status === "CLOSED") {
      payload.salePrice = parseDollars(form.get("salePrice"));
      payload.netToEstate = parseDollars(form.get("netToEstate"));
      payload.netNotes = String(form.get("netNotes") || "").trim() || null;
      payload.settlementUrl = String(form.get("settlementUrl") || "").trim() || null;
    }
    const res = await fetch(`/api/estates/${estateId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setPending(false);
      setError(data.error || "Could not save the snapshot.");
      return;
    }
    const closing = form.get("file");
    if (status === "CLOSED" && closing instanceof File && closing.size > 0) {
      const upload = await fetch(`/api/estates/${estateId}/closing-doc`, {
        method: "POST",
        credentials: "same-origin",
        body: form,
      });
      if (!upload.ok) {
        const uploadData = await upload.json().catch(() => ({}));
        setPending(false);
        setError(uploadData.error || "Snapshot saved, but the closing document did not upload.");
        return;
      }
    }
    setPending(false);
    setEditing(false);
    router.refresh();
  }

  return (
    <div className="mt-5 border-t border-line pt-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-forest">Property snapshot</h3>
        {canEdit && !editing && (
          <button type="button" className="text-sm font-semibold text-accent hover:underline" onClick={() => setEditing(true)}>
            Edit
          </button>
        )}
      </div>
      {editing ? (
        <form onSubmit={onSubmit} className="space-y-3">
          {comparePaths && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2 rounded-xl border border-line p-3">
                <p className="text-sm font-semibold text-forest">Cash path</p>
                <label className="block text-sm">
                  Cash offer range
                  <input
                    name="cashOfferRange"
                    defaultValue={snapshot.cashOfferRange ?? ""}
                    placeholder="Available within 48 hours"
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  Estimated net to estate
                  <input
                    name="cashNet"
                    defaultValue={snapshot.cashNet ?? ""}
                    inputMode="numeric"
                    placeholder="290000"
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  Speed & certainty note
                  <textarea
                    name="cashNotes"
                    defaultValue={snapshot.cashNotes ?? ""}
                    rows={2}
                    placeholder="Faster close, fewer surprises — usually a lower number than listing."
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
              </div>
              <div className="space-y-2 rounded-xl border border-line p-3">
                <p className="text-sm font-semibold text-forest">Market path</p>
                <label className="block text-sm">
                  Recommended list / CMA
                  <input
                    name="estimatedValue"
                    defaultValue={snapshot.estimatedValue ?? ""}
                    inputMode="numeric"
                    placeholder="349000"
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  Rough prep costs
                  <input
                    name="prepCosts"
                    defaultValue={snapshot.prepCosts ?? ""}
                    inputMode="numeric"
                    placeholder="8500"
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  Estimated net after costs & time
                  <input
                    name="marketNet"
                    defaultValue={snapshot.marketNet ?? ""}
                    inputMode="numeric"
                    placeholder="318000"
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  CMA note
                  <textarea
                    name="marketNotes"
                    defaultValue={snapshot.marketNotes ?? ""}
                    rows={2}
                    placeholder="We typically use a professional CMA unless an appraisal is required or preferred."
                    className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                  />
                </label>
              </div>
            </div>
          )}
          {status === "LISTED" && (
            <>
              <label className="block text-sm">
                List price
                <input
                  name="listPrice"
                  defaultValue={snapshot.listPrice ?? ""}
                  inputMode="numeric"
                  placeholder="349000"
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                RealTracs / listing link
                <input
                  name="listingUrl"
                  defaultValue={snapshot.listingUrl ?? ""}
                  placeholder="https://www.realtracs.com/..."
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
                <FieldHint>Family sees a “View listing” button.</FieldHint>
              </label>
              <label className="block text-sm">
                Listing notes
                <textarea
                  name="listingNotes"
                  defaultValue={snapshot.listingNotes ?? ""}
                  rows={2}
                  placeholder="As-is, lockbox on, showing instructions…"
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
              </label>
            </>
          )}
          {status === "UNDER_CONTRACT" && (
            <>
              <label className="block text-sm">
                Contract price
                <input
                  name="contractPrice"
                  defaultValue={snapshot.contractPrice ?? ""}
                  inputMode="numeric"
                  placeholder="340000"
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                Transaction status
                <select
                  name="transactionStatus"
                  defaultValue={snapshot.transactionStatus ?? "INSPECTION"}
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                >
                  {TX_STATUS_ORDER.map((value) => (
                    <option key={value} value={value}>
                      {TX_STATUS_LABEL[value]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                Contract details link
                <input
                  name="contractUrl"
                  defaultValue={snapshot.contractUrl ?? ""}
                  placeholder="https://..."
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
                <FieldHint>Optional. Family sees a “View contract details” button.</FieldHint>
              </label>
            </>
          )}
          {status === "CLOSED" && (
            <>
              <label className="block text-sm">
                Final sale price
                <input
                  name="salePrice"
                  defaultValue={snapshot.salePrice ?? ""}
                  inputMode="numeric"
                  placeholder="340000"
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
              </label>
              <label className="block text-sm font-semibold">
                Exact net to estate
                <input
                  name="netToEstate"
                  defaultValue={snapshot.netToEstate ?? ""}
                  inputMode="numeric"
                  placeholder="312000"
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                Closing documents link
                <input
                  name="settlementUrl"
                  defaultValue={snapshot.settlementUrl ?? ""}
                  placeholder="https://..."
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
                <FieldHint>
                  HUD, settlement statement, or title-company page. Family sees a “View closing documents” button.
                </FieldHint>
              </label>
              <label className="block text-sm">
                Or upload the settlement statement
                {snapshot.settlementFileName ? (
                  <span className="mt-1 block text-xs text-muted">
                    Current file: {snapshot.settlementFileName}
                  </span>
                ) : null}
                <input name="file" type="file" className="mt-1 w-full text-sm" />
              </label>
              <label className="block text-sm">
                Net notes
                <textarea
                  name="netNotes"
                  defaultValue={snapshot.netNotes ?? ""}
                  rows={2}
                  placeholder="After costs, commissions, and typical closing items. Not a full net sheet."
                  className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                />
              </label>
            </>
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
          <div className="flex gap-2">
            <button className="rounded-xl bg-forest px-3 py-2 text-sm font-semibold text-white" disabled={pending}>
              {pending ? "Saving…" : "Save"}
            </button>
            <button type="button" className="rounded-xl border border-line px-3 py-2 text-sm font-semibold" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div>
          {comparePaths && (
            <>
              <p className="mb-3 text-sm text-muted">
                Two ways to sell. Estimates only — not a full net sheet, and still subject to court
                approval.
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-line bg-warm-white p-3 text-sm">
                  <p className="font-semibold text-forest">Cash path</p>
                  <p className="mt-2 text-muted">Offer</p>
                  <p className="font-semibold text-forest">
                    {snapshot.cashOfferRange || "Cash offers available within 48 hours"}
                  </p>
                  <p className="mt-2 text-muted">Estimated net to estate</p>
                  <p className="font-semibold text-forest">{formatDollars(snapshot.cashNet)}</p>
                  <p className="mt-2 text-muted">
                    {snapshot.cashNotes ||
                      "Speed and certainty: as-is, fewer moving parts, often a lower number than listing."}
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-warm-white p-3 text-sm">
                  <p className="font-semibold text-forest">Market path</p>
                  <p className="mt-2 text-muted">Recommended list / CMA</p>
                  <p className="font-semibold text-forest">{formatDollars(snapshot.estimatedValue)}</p>
                  <p className="mt-2 text-muted">Rough prep costs</p>
                  <p className="font-semibold text-forest">{formatDollars(snapshot.prepCosts)}</p>
                  <p className="mt-2 text-muted">Estimated net after costs & time</p>
                  <p className="font-semibold text-forest">{formatDollars(snapshot.marketNet)}</p>
                  <p className="mt-2 text-muted">
                    {snapshot.marketNotes ||
                      "We typically use a professional CMA unless an appraisal is required or preferred by the family."}
                  </p>
                </div>
              </div>
            </>
          )}
          {!comparePaths && (
          <dl className="space-y-1 text-sm">
          {status === "LISTED" && (
            <>
              <SnapshotVerify
                href={snapshot.listingUrl ? hrefFor(snapshot.listingUrl) : null}
                label="View listing"
                emptyHint="Add a RealTracs / listing link so the family can verify."
                canEdit={canEdit}
              />
              <div className="flex justify-between gap-4">
                <dt className="text-muted">List price</dt>
                <dd className="font-semibold text-forest">{formatDollars(snapshot.listPrice)}</dd>
              </div>
              {snapshot.listingNotes ? <dd className="text-muted">{snapshot.listingNotes}</dd> : null}
            </>
          )}
          {status === "UNDER_CONTRACT" && (
            <>
              <SnapshotVerify
                href={snapshot.contractUrl ? hrefFor(snapshot.contractUrl) : null}
                label="View contract details"
                emptyHint="Add a contract details link so the family can verify."
                canEdit={canEdit}
              />
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Contract price</dt>
                <dd className="font-semibold text-forest">{formatDollars(snapshot.contractPrice)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Transaction status</dt>
                <dd className="font-semibold text-forest">
                  {snapshot.transactionStatus ? TX_STATUS_LABEL[snapshot.transactionStatus] : "—"}
                </dd>
              </div>
            </>
          )}
          {status === "CLOSED" && (
            <>
              <div className="mb-3 rounded-xl bg-mist px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Net to the estate</p>
                <p className="font-serif text-3xl font-bold text-forest">{formatDollars(snapshot.netToEstate)}</p>
              </div>
              <SnapshotVerify
                href={
                  snapshot.settlementUrl
                    ? hrefFor(snapshot.settlementUrl)
                    : snapshot.settlementFileName
                      ? `/api/estates/${estateId}/closing-doc`
                      : null
                }
                label="View closing documents"
                emptyHint="Add a closing documents link or upload the settlement statement so the family can verify."
                canEdit={canEdit}
              />
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Final sale price</dt>
                <dd className="font-semibold text-forest">{formatDollars(snapshot.salePrice)}</dd>
              </div>
              {snapshot.netNotes ? <dd className="text-muted">{snapshot.netNotes}</dd> : null}
            </>
          )}
        </dl>
          )}
        </div>
      )}
    </div>
  );
}

export function EstateAdminMenu({
  estateId,
  nickname,
}: {
  estateId: string;
  nickname: string;
}) {
  const [open, setOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        className="rounded-lg px-2 py-1 text-lg leading-none text-muted hover:bg-mist"
        aria-label="Estate settings"
        onClick={() => setOpen((v) => !v)}
      >
        ⋯
      </button>
      {open && !confirmOpen && (
        <div className="absolute right-0 z-10 mt-1 w-48 rounded-xl border border-line bg-white p-1 shadow-md">
          <button
            type="button"
            className="w-full rounded-lg px-3 py-2 text-left text-sm text-red-800 hover:bg-mist"
            onClick={() => {
              setOpen(false);
              setConfirmOpen(true);
            }}
          >
            Delete estate…
          </button>
        </div>
      )}
      {confirmOpen && (
        <div className="absolute right-0 z-10 mt-1 w-72 rounded-xl border border-line bg-white p-4 shadow-md">
          <p className="mb-3 text-sm font-semibold text-forest">Delete this estate?</p>
          <DeleteEstateForm estateId={estateId} nickname={nickname} />
          <button
            type="button"
            className="mt-2 text-sm text-muted hover:underline"
            onClick={() => setConfirmOpen(false)}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
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
