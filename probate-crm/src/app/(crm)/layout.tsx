import { redirect } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { getProfile } from "@/lib/leads";

export default async function CrmLayout({ children }: { children: React.ReactNode }) {
  const profile = await getProfile();
  if (!profile) redirect("/login");

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar profile={profile} />
      <main data-leads-scroll data-scroll-root className="min-h-screen flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
