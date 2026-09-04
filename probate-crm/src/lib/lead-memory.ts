"use client";

import { DEFAULT_FILTERS, isLeadListPath, leadListHref, type LeadListFilters } from "./lead-filters";

const RETURN_URL_KEY = "pg:leads:return-url";
const FILTERS_KEY = "pg:leads:filters";
const LAST_LEAD_KEY = "pg:leads:last-id";
const SCROLL_PREFIX = "pg:leads:scroll:";

function currentListUrl() {
  return `${window.location.pathname}${window.location.search}`;
}

export function peekLeadListReturnUrl() {
  if (typeof window === "undefined") return "/leads";
  try {
    const current = currentListUrl();
    if (isLeadListPath(current)) {
      rememberLeadListUrl(current);
      return current;
    }
    const stored = sessionStorage.getItem(RETURN_URL_KEY);
    if (stored && isLeadListPath(stored)) return stored;
    const raw = localStorage.getItem(FILTERS_KEY);
    if (raw) {
      const filters = JSON.parse(raw) as LeadListFilters;
      return leadListHref({ ...DEFAULT_FILTERS, ...filters });
    }
  } catch {
    // ignore storage errors
  }
  return "/leads";
}

export function rememberLeadListUrl(url?: string) {
  const value = url || currentListUrl();
  if (!isLeadListPath(value)) return;
  try {
    sessionStorage.setItem(RETURN_URL_KEY, value);
  } catch {
    // ignore
  }
}

export function persistLeadFilters(filters: LeadListFilters) {
  try {
    localStorage.setItem(FILTERS_KEY, JSON.stringify(filters));
    rememberLeadListUrl(leadListHref(filters));
  } catch {
    // ignore
  }
}

export function rememberOpenLead(leadId: string) {
  try {
    sessionStorage.setItem(LAST_LEAD_KEY, leadId);
  } catch {
    // ignore
  }
}

export function peekLastOpenLead() {
  try {
    return sessionStorage.getItem(LAST_LEAD_KEY);
  } catch {
    return null;
  }
}

function scrollKey(url?: string) {
  return `${SCROLL_PREFIX}${url || currentListUrl()}`;
}

function scrollContainers(): HTMLElement[] {
  const nodes: HTMLElement[] = [];
  const main = document.querySelector("[data-leads-scroll], main, [data-scroll-root]");
  if (main instanceof HTMLElement) nodes.push(main);
  if (document.scrollingElement instanceof HTMLElement) nodes.push(document.scrollingElement);
  if (document.documentElement) nodes.push(document.documentElement);
  if (document.body) nodes.push(document.body);
  return nodes;
}

export function readScrollTop() {
  const fromWindow = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
  for (const node of scrollContainers()) {
    if (node.scrollTop > 0) return node.scrollTop;
  }
  return fromWindow;
}

export function writeScrollTop(top: number) {
  window.scrollTo(0, top);
  document.documentElement.scrollTop = top;
  document.body.scrollTop = top;
  for (const node of scrollContainers()) {
    node.scrollTop = top;
  }
}

export function saveLeadListScroll(url?: string, leadId?: string) {
  const value = url || currentListUrl();
  if (!isLeadListPath(value)) return;
  try {
    const top = Math.round(readScrollTop());
    sessionStorage.setItem(scrollKey(value), String(top));
    sessionStorage.setItem(RETURN_URL_KEY, value);
    if (leadId) sessionStorage.setItem(LAST_LEAD_KEY, leadId);
  } catch {
    // ignore
  }
}

export function restoreLeadListScroll(url?: string) {
  const value = url || currentListUrl();
  if (!isLeadListPath(value)) return;
  try {
    const raw = sessionStorage.getItem(scrollKey(value));
    if (raw == null) {
      const leadId = peekLastOpenLead();
      if (leadId) {
        document.getElementById(`lead-card-${leadId}`)?.scrollIntoView({ block: "center" });
      }
      return;
    }
    const top = Number(raw);
    if (!Number.isFinite(top)) return;
    writeScrollTop(top);
    const leadId = peekLastOpenLead();
    if (leadId) {
      const card = document.getElementById(`lead-card-${leadId}`);
      if (card) {
        const rect = card.getBoundingClientRect();
        const inView = rect.top >= 80 && rect.bottom <= window.innerHeight - 40;
        if (!inView) card.scrollIntoView({ block: "center" });
      }
    }
  } catch {
    // ignore
  }
}
