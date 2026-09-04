export const CALL_LIST_FILTER = "call_list";
export const ALL_STATUSES_FILTER = "all";
export const CALLED_OLDEST = "oldest";
export const CALLED_NEWEST = "newest";
export const CALLED_NEVER = "never";
export const DUE_ANY = "any";
export const DUE_FOLLOW_UP = "follow_up";
export const MAILER_ANY = "any";
export const MAILER_NEEDS = "needs";

export type LeadListFilters = {
  status: string;
  called: string;
  due: string;
  mailer: string;
  q?: string;
  county?: string;
};

export const DEFAULT_FILTERS: LeadListFilters = {
  status: CALL_LIST_FILTER,
  called: CALLED_OLDEST,
  due: DUE_ANY,
  mailer: MAILER_ANY,
};

export function parseLeadFilters(searchParams: Record<string, string | string[] | undefined>): LeadListFilters {
  const get = (key: string) => {
    const value = searchParams[key];
    return Array.isArray(value) ? value[0] : value;
  };
  return {
    status: get("status") || DEFAULT_FILTERS.status,
    called: get("called") || DEFAULT_FILTERS.called,
    due: get("due") || DEFAULT_FILTERS.due,
    mailer: get("mailer") || DEFAULT_FILTERS.mailer,
    q: get("q") || "",
    county: get("county") || "",
  };
}

export function leadListHref(filters: LeadListFilters) {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== DEFAULT_FILTERS.status) params.set("status", filters.status);
  if (filters.called && filters.called !== DEFAULT_FILTERS.called) params.set("called", filters.called);
  if (filters.due && filters.due !== DEFAULT_FILTERS.due) params.set("due", filters.due);
  if (filters.mailer && filters.mailer !== DEFAULT_FILTERS.mailer) params.set("mailer", filters.mailer);
  if (filters.county) params.set("county", filters.county);
  if (filters.q) params.set("q", filters.q);
  const qs = params.toString();
  return qs ? `/leads?${qs}` : "/leads";
}

export function isLeadListPath(url: string) {
  const path = (url.split("?")[0] || "/").replace(/\/+$/, "") || "/";
  return path === "/leads";
}
