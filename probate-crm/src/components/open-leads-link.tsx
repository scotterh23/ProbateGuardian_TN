"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { peekLeadListReturnUrl } from "@/lib/lead-memory";

export function OpenLeadsLink({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const router = useRouter();
  const [href, setHref] = useState("/leads");

  useEffect(() => {
    setHref(peekLeadListReturnUrl());
  }, []);

  return (
    <a
      href={href}
      className={className}
      onClick={(event) => {
        event.preventDefault();
        router.push(peekLeadListReturnUrl(), { scroll: false });
      }}
    >
      {children}
    </a>
  );
}
