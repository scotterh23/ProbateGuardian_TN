import { BackToLeads, SimplePage } from "../simple-pages";

export default function SettingsPage() {
  return (
    <SimplePage title="Settings">
      <p className="text-sm text-muted">Account and org settings stay on the live CRM. This Round 2 ship is the leads calling workflow.</p>
      <BackToLeads />
    </SimplePage>
  );
}
