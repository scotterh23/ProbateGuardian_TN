"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { peekLeadListReturnUrl } from "@/lib/lead-memory";

export function LeadBackLink() {
  const router = useRouter();
  const [href, setHref] = useState("/leads");

  useEffect(() => {
    setHref(peekLeadListReturnUrl());
  }, []);

  return (
    <a
      href={href}
      aria-label="Back to leads list"
      title="Back to the leads list — keeps your filters and place"
      className="relative z-50 inline-flex h-10 w-10 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      onClick={(event) => {
        event.preventDefault();
        router.push(peekLeadListReturnUrl(), { scroll: false });
      }}
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="m12 19-7-7 7-7" />
        <path d="M19 12H5" />
      </svg>
    </a>
  );
}
