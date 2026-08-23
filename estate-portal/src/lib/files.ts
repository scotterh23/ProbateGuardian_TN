import { mkdir, writeFile, readFile } from "fs/promises";
import path from "path";
import { randomUUID } from "crypto";

const UPLOAD_DIR = path.join(process.cwd(), "uploads");
export const MAX_UPLOAD_BYTES = 12 * 1024 * 1024;

export function getUploadedFile(form: FormData, key = "file"): File | null {
  const value = form.get(key);
  if (!value || typeof value === "string") return null;
  const file = value as File;
  if (typeof file.arrayBuffer !== "function") return null;
  if (!Number(file.size)) return null;
  return file;
}

export async function saveUpload(file: File) {
  await mkdir(UPLOAD_DIR, { recursive: true });
  const ext = path.extname(file.name || "").slice(0, 12);
  const stored = `${randomUUID()}${ext}`;
  const full = path.join(UPLOAD_DIR, stored);
  const buf = Buffer.from(await file.arrayBuffer());
  await writeFile(full, buf);
  return {
    storedName: stored,
    fileName: file.name || stored,
    mime: file.type || "application/octet-stream",
    size: buf.length,
  };
}

export async function readUpload(storedName: string) {
  const full = path.join(UPLOAD_DIR, path.basename(storedName));
  return readFile(full);
}
