import { EstateProgress, EstateStatus, UserRole } from "@prisma/client";

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

export const PROGRESS_ORDER: EstateProgress[] = [
  "LETTERS_ISSUED",
  "INVENTORY_FILED",
  "NOTICE_TO_CREDITORS",
  "CREDITOR_PERIOD_ENDED",
  "DEBTS_TAXES_SETTLED",
  "FINAL_ACCOUNTING",
  "ESTATE_CLOSED",
];

export const PROGRESS_LABEL: Record<EstateProgress, string> = {
  LETTERS_ISSUED: "Letters Issued",
  INVENTORY_FILED: "Inventory Filed",
  NOTICE_TO_CREDITORS: "Notice to Creditors Published",
  CREDITOR_PERIOD_ENDED: "Creditor Period Ended",
  DEBTS_TAXES_SETTLED: "Debts & Taxes Settled",
  FINAL_ACCOUNTING: "Final Accounting Submitted",
  ESTATE_CLOSED: "Estate Closed",
};

export const PROGRESS_HELP: Record<EstateProgress, string> = {
  LETTERS_ISSUED:
    "The court has named someone to act for the estate. The house can typically be listed at this stage, subject to court rules and your attorney’s guidance.",
  INVENTORY_FILED:
    "A list of what the estate owns has been prepared and filed — bank accounts, the house, vehicles, and other assets.",
  NOTICE_TO_CREDITORS:
    "A public notice tells people who are owed money that the estate is open, so they have a chance to come forward.",
  CREDITOR_PERIOD_ENDED:
    "The waiting window for claims has run. This is the much safer window to close a house sale — still subject to court approval, not a guarantee.",
  DEBTS_TAXES_SETTLED:
    "Known bills, taxes, and valid claims are being paid from estate funds so the rest can go to heirs.",
  FINAL_ACCOUNTING:
    "A closing report shows what came in, what was paid, and what remains to distribute. The court reviews it.",
  ESTATE_CLOSED:
    "The court has ended the probate case. Remaining assets, if any, can be distributed per the will or Tennessee law.",
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
