import { EstateStatus, UserRole } from "@prisma/client";

export const STATUS_ORDER: EstateStatus[] = [
  "LETTERS",
  "VALUATION",
  "LISTED",
  "UNDER_CONTRACT",
  "CLOSED",
];

export const STATUS_LABEL: Record<EstateStatus, string> = {
  LETTERS: "Letters issued",
  VALUATION: "Valuation",
  LISTED: "Listed",
  UNDER_CONTRACT: "Under contract",
  CLOSED: "Closed",
};

export const ROLE_LABEL: Record<UserRole, string> = {
  ADMIN: "Probate Guardians",
  EXECUTOR: "Executor",
  HEIR: "Heir",
  ATTORNEY: "Attorney",
};

export const DOC_LABEL: Record<string, string> = {
  WILL: "Will",
  LETTERS: "Letters Testamentary",
  APPRAISAL: "Appraisal / CMA",
  PHOTOS: "Photos",
  CONTRACTS: "Contracts",
  OTHER: "Other",
};

export function formatDate(value: Date | string) {
  const d = typeof value === "string" ? new Date(value) : value;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(value: Date | string) {
  const d = typeof value === "string" ? new Date(value) : value;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
