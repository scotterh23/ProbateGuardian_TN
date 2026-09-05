import { BackToLeads, SimplePage } from "../simple-pages";

export default function DripPage() {
  return (
    <SimplePage title="Drip Campaigns">
      <p className="text-sm text-muted">Drip enrollment is unchanged. Log emails from the lead page so last-email stays visible next to mailer and call history.</p>
      <BackToLeads />
    </SimplePage>
  );
}
