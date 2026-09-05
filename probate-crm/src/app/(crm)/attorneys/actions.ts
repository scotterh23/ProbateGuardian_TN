"use server";

import { revalidatePath } from "next/cache";
import {
  ATTORNEY_CONTACT_FIELDS,
  contactPatchFromForm,
  isAttorneyId,
  parseAttorneyContactCsv,
  planAttorneyContactUpdates,
  type AttorneyContactField,
  type AttorneyContactPatch,
} from "@/lib/attorney-contact";
import { loadAttorney, loadAttorneys } from "@/lib/attorneys";
import { createClient } from "@/lib/supabase/server";

async function requireUser() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not signed in");
  return { supabase, user };
}

function assertAttorneyOnlyPatch(patch: AttorneyContactPatch) {
  for (const key of Object.keys(patch)) {
    if (!ATTORNEY_CONTACT_FIELDS.includes(key as AttorneyContactField)) {
      throw new Error(`Refusing to write unknown attorney field: ${key}`);
    }
  }
}

async function updateAttorneyRow(id: string, patch: AttorneyContactPatch) {
  if (!isAttorneyId(id)) throw new Error("Invalid attorney id");
  assertAttorneyOnlyPatch(patch);
  if (!Object.keys(patch).length) return { updated: false };

  const { supabase } = await requireUser();
  const { data, error } = await supabase
    .from("attorneys")
    .update({ ...patch, updated_at: new Date().toISOString() })
    .eq("id", id)
    .select("id")
    .maybeSingle();
  if (error) throw new Error(error.message);
  if (!data) throw new Error("Attorney not found — nothing created");
  revalidatePath("/attorneys");
  revalidatePath(`/attorneys/${id}`);
  return { updated: true };
}

export async function updateAttorneyContact(
  attorneyId: string,
  incoming: Partial<Record<AttorneyContactField, string | undefined>>,
  clear: Partial<Record<AttorneyContactField, boolean | undefined>> = {},
) {
  const current = await loadAttorney(attorneyId);
  if (!current) throw new Error("Attorney not found — nothing created");
  const patch = contactPatchFromForm(incoming, clear);
  return updateAttorneyRow(attorneyId, patch);
}

export async function updateAttorneyContactForm(attorneyId: string, formData: FormData) {
  const incoming: Partial<Record<AttorneyContactField, string>> = {};
  const clear: Partial<Record<AttorneyContactField, boolean>> = {};
  for (const field of ATTORNEY_CONTACT_FIELDS) {
    incoming[field] = String(formData.get(field) || "");
    clear[field] = formData.get(`clear_${field}`) === "on";
  }
  await updateAttorneyContact(attorneyId, incoming, clear);
}

export async function previewAttorneyContactImport(csvText: string) {
  await requireUser();
  const parsed = parseAttorneyContactCsv(csvText);
  const attorneys = parsed.rows.length ? await loadAttorneys() : [];
  const planned = planAttorneyContactUpdates(attorneys, parsed.rows);
  return {
    updateCount: planned.updates.length,
    updates: planned.updates,
    skipped: [...parsed.skipped, ...planned.skipped],
  };
}

export async function applyAttorneyContactImport(csvText: string) {
  const preview = await previewAttorneyContactImport(csvText);
  let updated = 0;
  for (const row of preview.updates) {
    const result = await updateAttorneyRow(row.id, row.patch);
    if (result.updated) updated += 1;
  }
  revalidatePath("/attorneys");
  return { updated, skipped: preview.skipped.length };
}
