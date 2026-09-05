import { OpenLeadsLink } from "@/components/open-leads-link";

export function SimplePage({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <h1 className="text-2xl font-semibold">{title}</h1>
      {children}
    </div>
  );
}

export function BackToLeads() {
  return (
    <p className="text-sm">
      <OpenLeadsLink className="font-medium text-primary hover:underline">Open Leads</OpenLeadsLink> to
      keep calling. Filters and scroll stay on the Leads page.
    </p>
  );
}
