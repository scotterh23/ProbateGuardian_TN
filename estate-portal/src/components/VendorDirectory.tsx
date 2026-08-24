"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { VendorCategory } from "@prisma/client";
import { VENDOR_CATEGORY_LABEL, VENDOR_CATEGORY_ORDER } from "@/lib/status";

export type VendorCard = {
  id: string;
  category: VendorCategory;
  name: string;
  description: string;
  phone: string | null;
  email: string | null;
  serviceArea: string | null;
  notes: string | null;
};

export function VendorDirectory({
  estateId,
  vendors,
  canManage,
}: {
  estateId: string;
  vendors: VendorCard[];
  canManage: boolean;
}) {
  const router = useRouter();
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [pendingIntro, setPendingIntro] = useState("");

  async function requestIntro(vendorId: string) {
    setNotice("");
    setError("");
    setPendingIntro(vendorId);
    const res = await fetch(`/api/vendors/${vendorId}/intro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ estateId }),
    });
    const data = await res.json().catch(() => ({}));
    setPendingIntro("");
    if (!res.ok) {
      setError(data.message || data.error || "Could not request an introduction.");
      return;
    }
    setNotice(data.message);
  }

  async function removeVendor(id: string, name: string) {
    if (!confirm(`Remove ${name} from the recommended list?`)) return;
    const res = await fetch(`/api/vendors/${id}`, { method: "DELETE", credentials: "same-origin" });
    if (!res.ok) {
      setError("Could not remove that vendor.");
      return;
    }
    router.refresh();
  }

  return (
    <section className="card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="section-title">Recommended Vendors</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            These are professionals we regularly work with on probate properties. You can request an
            introduction or contact them directly.
          </p>
        </div>
        {canManage && (
          <button
            type="button"
            className="rounded-xl border border-line px-3 py-2 text-sm font-semibold"
            onClick={() => {
              setAdding((v) => !v);
              setEditingId(null);
            }}
          >
            {adding ? "Cancel" : "Add vendor"}
          </button>
        )}
      </div>
      {notice && <p className="mt-3 text-sm font-medium text-forest">{notice}</p>}
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      {canManage && adding && (
        <div className="mt-4">
          <VendorForm
            onDone={() => {
              setAdding(false);
              router.refresh();
            }}
          />
        </div>
      )}
      {vendors.length === 0 && !adding ? (
        <p className="mt-4 text-sm text-muted">No vendors listed yet.</p>
      ) : (
        <div className="mt-6 space-y-8">
          {VENDOR_CATEGORY_ORDER.map((category) => {
            const group = vendors.filter((v) => v.category === category);
            if (group.length === 0 && !canManage) return null;
            if (group.length === 0) return null;
            return (
              <div key={category}>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
                  {VENDOR_CATEGORY_LABEL[category]}
                </h3>
                <ul className="grid gap-3 md:grid-cols-2">
                  {group.map((vendor) => (
                    <li key={vendor.id} className="rounded-xl border border-line bg-warm-white p-4">
                      {editingId === vendor.id ? (
                        <VendorForm
                          vendor={vendor}
                          onDone={() => {
                            setEditingId(null);
                            router.refresh();
                          }}
                          onCancel={() => setEditingId(null)}
                        />
                      ) : (
                        <>
                          <div className="flex items-start justify-between gap-2">
                            <h4 className="font-semibold text-forest">{vendor.name}</h4>
                            <span className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 text-xs font-semibold text-accent">
                              Recommended by Probate Guardians
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-muted">{vendor.description}</p>
                          {vendor.serviceArea && (
                            <p className="mt-2 text-sm text-muted">Service area: {vendor.serviceArea}</p>
                          )}
                          {vendor.notes && <p className="mt-1 text-sm text-muted">{vendor.notes}</p>}
                          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                            {vendor.phone && (
                              <a className="font-semibold text-accent hover:underline" href={`tel:${vendor.phone}`}>
                                {vendor.phone}
                              </a>
                            )}
                            {vendor.email && (
                              <a className="font-semibold text-accent hover:underline" href={`mailto:${vendor.email}`}>
                                {vendor.email}
                              </a>
                            )}
                            <button
                              type="button"
                              className="rounded-xl bg-forest px-3 py-1.5 font-semibold text-white disabled:opacity-60"
                              disabled={pendingIntro === vendor.id}
                              onClick={() => requestIntro(vendor.id)}
                            >
                              {pendingIntro === vendor.id ? "Sending…" : "Request introduction"}
                            </button>
                            {canManage && (
                              <>
                                <button
                                  type="button"
                                  className="text-sm font-semibold text-forest hover:underline"
                                  onClick={() => setEditingId(vendor.id)}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="text-sm font-semibold text-red-800 hover:underline"
                                  onClick={() => removeVendor(vendor.id, vendor.name)}
                                >
                                  Remove
                                </button>
                              </>
                            )}
                          </div>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function VendorForm({
  vendor,
  onDone,
  onCancel,
}: {
  vendor?: VendorCard;
  onDone: () => void;
  onCancel?: () => void;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const form = new FormData(e.currentTarget);
    const payload = {
      category: form.get("category"),
      name: form.get("name"),
      description: form.get("description"),
      phone: String(form.get("phone") || "") || null,
      email: String(form.get("email") || "") || null,
      serviceArea: String(form.get("serviceArea") || "") || null,
      notes: String(form.get("notes") || "") || null,
    };
    const res = await fetch(vendor ? `/api/vendors/${vendor.id}` : "/api/vendors", {
      method: vendor ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not save this vendor.");
      return;
    }
    onDone();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-xl border border-line bg-white p-4">
      <label className="block text-sm">
        Category
        <select
          name="category"
          defaultValue={vendor?.category || "ESTATE_SALE"}
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        >
          {VENDOR_CATEGORY_ORDER.map((value) => (
            <option key={value} value={value}>
              {VENDOR_CATEGORY_LABEL[value]}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        Name
        <input name="name" required defaultValue={vendor?.name} className="mt-1 w-full rounded-xl border border-line px-3 py-2" />
      </label>
      <label className="block text-sm">
        Short description
        <textarea
          name="description"
          required
          minLength={8}
          rows={2}
          defaultValue={vendor?.description}
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        />
      </label>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          Phone
          <input name="phone" defaultValue={vendor?.phone ?? ""} className="mt-1 w-full rounded-xl border border-line px-3 py-2" />
        </label>
        <label className="block text-sm">
          Email
          <input name="email" type="email" defaultValue={vendor?.email ?? ""} className="mt-1 w-full rounded-xl border border-line px-3 py-2" />
        </label>
      </div>
      <label className="block text-sm">
        Service area
        <input
          name="serviceArea"
          defaultValue={vendor?.serviceArea ?? ""}
          placeholder="Middle Tennessee"
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        />
      </label>
      <label className="block text-sm">
        Notes
        <input name="notes" defaultValue={vendor?.notes ?? ""} className="mt-1 w-full rounded-xl border border-line px-3 py-2" />
      </label>
      {error && <p className="text-sm text-red-700">{error}</p>}
      <div className="flex gap-2">
        <button className="rounded-xl bg-forest px-3 py-2 text-sm font-semibold text-white" disabled={pending}>
          {pending ? "Saving…" : vendor ? "Save" : "Add vendor"}
        </button>
        {onCancel && (
          <button type="button" className="rounded-xl border border-line px-3 py-2 text-sm font-semibold" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
