export function supabaseUrl() {
  const url = (process.env.NEXT_PUBLIC_SUPABASE_URL ?? "https://ayspneolhplcufdhrwfu.supabase.co").trim();
  return url;
}

export function supabaseAnonKey() {
  const key = (
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5c3BuZW9saHBsY3VmZGhyd2Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjYzNzcsImV4cCI6MjA5OTEwMjM3N30.95QgvJlvfd3wvCIC0tM6OQuY17DeX5PhzdRHRIfDlvo"
  ).trim();
  return key;
}
