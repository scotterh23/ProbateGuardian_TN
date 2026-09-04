"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signOut } from "@/app/(crm)/leads/actions";
import { peekLeadListReturnUrl } from "@/lib/lead-memory";
import type { Profile } from "@/lib/types";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/leads", label: "Leads" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/cases", label: "Cases" },
  { href: "/attorneys", label: "Attorneys" },
  { href: "/call-queue", label: "Call Queue" },
  { href: "/mailer-queue", label: "Mailer Queue" },
  { href: "/import", label: "Paste Import" },
  { href: "/drip", label: "Drip Campaigns" },
  { href: "/partners", label: "Partners" },
];

const ADMIN_NAV = [
  { href: "/agents", label: "Agents" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar({ profile }: { profile: Profile }) {
  const pathname = usePathname();
  const router = useRouter();
  const [leadsHref, setLeadsHref] = useState("/leads");
  const items = profile.role === "admin" ? [...NAV, ...ADMIN_NAV] : NAV;

  useEffect(() => {
    setLeadsHref(peekLeadListReturnUrl());
  }, [pathname]);

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-sidebar text-slate-200">
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-white">PG</div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-white">Probate CRM Pro</h1>
          <p className="text-xs capitalize text-slate-400">{profile.role || "member"}</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const href = item.href === "/leads" ? leadsHref : item.href;
          return (
            <Link
              key={item.href}
              href={href}
              scroll={item.href !== "/leads"}
              onClick={(event) => {
                if (item.href !== "/leads") return;
                event.preventDefault();
                const next = peekLeadListReturnUrl();
                setLeadsHref(next);
                router.push(next, { scroll: false });
              }}
              className={`flex items-center rounded-lg px-3 py-2.5 text-sm font-medium ${
                active ? "bg-primary text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-slate-800 p-4">
        <p className="px-3 text-sm font-medium text-white">{profile.full_name || "Team"}</p>
        <p className="mb-3 px-3 text-xs text-slate-400">{profile.email}</p>
        <form action={signOut}>
          <button type="submit" className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-800">
            Sign Out
          </button>
        </form>
      </div>
    </aside>
  );
}
