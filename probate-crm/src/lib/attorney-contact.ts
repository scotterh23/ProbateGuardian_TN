import type { Attorney } from "@/lib/types";

export const ATTORNEY_CONTACT_FIELDS = ["firm", "email", "phone", "county", "address"] as const;
export type AttorneyContactField = (typeof ATTORNEY_CONTACT_FIELDS)[number];

export type AttorneyContactPatch = Partial<Record<AttorneyContactField, string | null>>;

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ID_HEADERS = new Set(["attorney_id", "attorneyid", "id"]);

export function isAttorneyId(value: string) {
  return UUID_RE.test(value.trim());
}

export function normalizeContactValue(value: string | null | undefined) {
  const trimmed = (value ?? "").trim();
  return trimmed ? trimmed : "";
}

export function contactPatchFromForm(
  incoming: Partial<Record<AttorneyContactField, string | undefined>>,
  clear: Partial<Record<AttorneyContactField, boolean | undefined>>,
): AttorneyContactPatch {
  const patch: AttorneyContactPatch = {};
  for (const field of ATTORNEY_CONTACT_FIELDS) {
    if (clear[field]) {
      patch[field] = null;
      continue;
    }
    const value = normalizeContactValue(incoming[field]);
    if (!value) continue;
    patch[field] = value;
  }
  return patch;
}

export type AttorneyImportRow = {
  line: number;
  attorney_id: string;
  values: AttorneyContactPatch;
};

export type AttorneyImportSkip = {
  line: number;
  attorney_id?: string;
  reason: string;
};

export type AttorneyImportChange = {
  field: AttorneyContactField;
  from: string | null;
  to: string | null;
};

export type AttorneyImportUpdate = {
  id: string;
  name: string;
  changes: AttorneyImportChange[];
  patch: AttorneyContactPatch;
};

function parseDelimitedLine(line: string, delimiter: string) {
  const cells: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === delimiter && !inQuotes) {
      cells.push(current);
      current = "";
      continue;
    }
    current += ch;
  }
  cells.push(current);
  return cells.map((cell) => cell.trim());
}

function detectDelimiter(headerLine: string) {
  const comma = (headerLine.match(/,/g) || []).length;
  const tab = (headerLine.match(/\t/g) || []).length;
  const semi = (headerLine.match(/;/g) || []).length;
  if (tab > comma && tab >= semi) return "\t";
  if (semi > comma && semi > tab) return ";";
  return ",";
}

function normalizeHeader(value: string) {
  return value.trim().toLowerCase().replace(/[\s-]+/g, "_");
}

export function parseAttorneyContactCsv(text: string): { rows: AttorneyImportRow[]; skipped: AttorneyImportSkip[] } {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/);
  const skipped: AttorneyImportSkip[] = [];
  const rows: AttorneyImportRow[] = [];
  let headerIndex = -1;
  let delimiter = ",";
  let headers: string[] = [];

  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i].trim()) {
      headerIndex = i;
      delimiter = detectDelimiter(lines[i]);
      headers = parseDelimitedLine(lines[i], delimiter).map(normalizeHeader);
      break;
    }
  }
  if (headerIndex < 0) return { rows, skipped };

  const idIndex = headers.findIndex((header) => ID_HEADERS.has(header));
  if (idIndex < 0) {
    skipped.push({ line: headerIndex + 1, reason: "Missing attorney_id column" });
    return { rows, skipped };
  }

  const fieldIndexes = new Map<AttorneyContactField, number>();
  for (const field of ATTORNEY_CONTACT_FIELDS) {
    const index = headers.findIndex((header) => header === field);
    if (index >= 0) fieldIndexes.set(field, index);
  }

  for (let i = headerIndex + 1; i < lines.length; i += 1) {
    if (!lines[i].trim()) continue;
    const cells = parseDelimitedLine(lines[i], delimiter);
    const attorneyId = (cells[idIndex] || "").trim();
    if (!attorneyId) {
      skipped.push({ line: i + 1, reason: "Blank attorney_id" });
      continue;
    }
    if (!isAttorneyId(attorneyId)) {
      skipped.push({ line: i + 1, attorney_id: attorneyId, reason: "attorney_id is not a UUID" });
      continue;
    }
    const values: AttorneyContactPatch = {};
    for (const [field, index] of fieldIndexes) {
      const value = normalizeContactValue(cells[index]);
      if (value) values[field] = value;
    }
    if (!Object.keys(values).length) {
      skipped.push({ line: i + 1, attorney_id: attorneyId, reason: "No non-empty contact fields" });
      continue;
    }
    rows.push({ line: i + 1, attorney_id: attorneyId, values });
  }

  return { rows, skipped };
}

export function planAttorneyContactUpdates(existing: Attorney[], incoming: AttorneyImportRow[]) {
  const byId = new Map(existing.map((row) => [row.id, row]));
  const updates: AttorneyImportUpdate[] = [];
  const skipped: AttorneyImportSkip[] = [];

  for (const row of incoming) {
    const attorney = byId.get(row.attorney_id);
    if (!attorney) {
      skipped.push({ line: row.line, attorney_id: row.attorney_id, reason: "No attorney with this id — not created" });
      continue;
    }
    const patch: AttorneyContactPatch = {};
    const changes: AttorneyImportChange[] = [];
    for (const field of ATTORNEY_CONTACT_FIELDS) {
      const next = row.values[field];
      if (next == null || next === "") continue;
      const current = attorney[field] ?? null;
      if ((current || "") === next) continue;
      patch[field] = next;
      changes.push({ field, from: current, to: next });
    }
    if (!changes.length) {
      skipped.push({ line: row.line, attorney_id: row.attorney_id, reason: "Already matches — no overwrite" });
      continue;
    }
    updates.push({
      id: attorney.id,
      name: attorney.full_name || "Unnamed attorney",
      changes,
      patch,
    });
  }

  return { updates, skipped };
}
