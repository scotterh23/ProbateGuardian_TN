export function publicAppOrigin(req: Request) {
  const forwardedHost = req.headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const forwardedProto = req.headers.get("x-forwarded-proto")?.split(",")[0]?.trim();
  if (forwardedHost) {
    const host = forwardedHost.replace(/:443$/, "");
    return `${forwardedProto || "https"}://${host}`;
  }
  const env = process.env.AUTH_URL;
  if (env) {
    try {
      const url = new URL(env);
      if (!url.hostname.includes("localhost") && url.hostname !== "127.0.0.1") {
        return url.origin;
      }
    } catch {
      /* ignore malformed AUTH_URL */
    }
  }
  return new URL(req.url).origin;
}
