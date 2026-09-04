import { BackToLeads, SimplePage } from "../simple-pages";

export default function ImportPage() {
  return (
    <SimplePage title="Paste Import">
      <p className="text-sm text-muted">Import stays on the current production workflow. Use Leads for calling.</p>
      <BackToLeads />
    </SimplePage>
  );
}
