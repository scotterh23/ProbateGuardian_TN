import Image from "next/image";
import Link from "next/link";

export function BrandLogo({
  href = "/dashboard",
  size = "header",
}: {
  href?: string | null;
  size?: "header" | "hero";
}) {
  const isHero = size === "hero";
  const mark = (
    <span className="inline-flex items-center gap-2.5">
      <Image
        src="/images/pg-logo.png"
        alt=""
        width={isHero ? 88 : 40}
        height={isHero ? 88 : 40}
        className={isHero ? "h-[88px] w-[88px] object-contain" : "h-10 w-10 object-contain"}
        priority
      />
      <span className={isHero ? "text-left" : ""}>
        <span className={`block font-serif font-semibold leading-tight text-forest ${isHero ? "text-2xl" : "text-base"}`}>
          Probate Guardians <span className="text-forest-600">TN</span>
        </span>
        <span className={`block tracking-wide text-muted ${isHero ? "text-sm" : "text-xs"}`}>
          Estate Portal
        </span>
      </span>
    </span>
  );

  if (!href) return mark;
  return (
    <Link href={href} className="inline-flex items-center no-underline" aria-label="Probate Guardians Estate Portal">
      {mark}
    </Link>
  );
}
