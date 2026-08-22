import { mkdir, writeFile, readFile } from "fs/promises";
import path from "path";
import { randomUUID } from "crypto";

const UPLOAD_DIR = path.join(process.cwd(), "uploads");

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
