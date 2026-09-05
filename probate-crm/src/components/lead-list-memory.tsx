"use client";

import { useLayoutEffect } from "react";
import { persistLeadFilters, rememberLeadListUrl, restoreLeadListScroll, saveLeadListScroll } from "@/lib/lead-memory";
import type { LeadListFilters } from "@/lib/lead-filters";
import { leadListHref } from "@/lib/lead-filters";

export function LeadListMemory({ filters }: { filters: LeadListFilters }) {
  const href = leadListHref(filters);

  useLayoutEffect(() => {
    try {
      window.history.scrollRestoration = "manual";
    } catch {
      // ignore
    }
    persistLeadFilters(filters);
    rememberLeadListUrl(href);

    let restoring = false;
    let lockRestore = false;

    const restore = () => {
      if (lockRestore) return;
      restoring = true;
      restoreLeadListScroll(href);
      requestAnimationFrame(() => {
        restoring = false;
      });
    };

    restore();
    const timers = [50, 150, 400].map((ms) => window.setTimeout(restore, ms));

    const onScroll = () => {
      if (restoring) return;
      lockRestore = true;
      saveLeadListScroll(href);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("scroll", onScroll, { passive: true, capture: true });
    window.addEventListener("pagehide", onScroll);
    return () => {
      timers.forEach((id) => window.clearTimeout(id));
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("pagehide", onScroll);
    };
  }, [href, filters]);

  return null;
}
