import { mkdir, writeFile, readFile, unlink } from "fs/promises";
import path from "path";
import { randomUUID } from "crypto";
import { del, get, put } from "@vercel/blob";

const UPLOAD_DIR = path.join(process.cwd(), "uploads");
export const MAX_UPLOAD_BYTES = 12 * 1024 * 1024;
const BLOB_PREFIX = "estate-portal/";

function blobEnabled() {
  return Boolean(
    process.env.BLOB_READ_WRITE_TOKEN ||
      (process.env.VERCEL === "1" && process.env.BLOB_STORE_ID),
  );
}

export function getUploadedFile(form: FormData, key = "file"): File | null {
  const value = form.get(key);
  if (!value || typeof value === "string") return null;
  const file = value as File;
  if (typeof file.arrayBuffer !== "function") return null;
  if (!Number(file.size)) return null;
  return file;
}

export async function saveUpload(file: File) {
  const ext = path.extname(file.name || "").replace(/[^\w.]/g, "").slice(0, 12);
  const stored = `${randomUUID()}${ext}`;
  const buf = Buffer.from(await file.arrayBuffer());
  const mime = file.type || "application/octet-stream";
  const fileName = file.name || stored;

  if (blobEnabled()) {
    const pathname = `${BLOB_PREFIX}${stored}`;
    const blob = await put(pathname, buf, {
      access: "private",
      addRandomSuffix: false,
      contentType: mime,
    });
    return {
      storedName: blob.pathname || pathname,
      fileName,
      mime,
      size: buf.length,
    };
  }

  await mkdir(UPLOAD_DIR, { recursive: true });
  await writeFile(path.join(UPLOAD_DIR, stored), buf);
  return { storedName: stored, fileName, mime, size: buf.length };
}

export async function readUpload(storedName: string) {
  if (blobEnabled() || storedName.includes("/") || storedName.startsWith("http")) {
    const result = await get(storedName, { access: "private" });
    if (!result?.stream) {
      throw new Error("File not found in blob storage.");
    }
    return Buffer.from(await new Response(result.stream).arrayBuffer());
  }
  const full = path.join(UPLOAD_DIR, path.basename(storedName));
  return readFile(full);
}

export async function removeUpload(storedName: string) {
  if (!storedName) return;
  if (blobEnabled() || storedName.includes("/") || storedName.startsWith("http")) {
    try {
      await del(storedName);
    } catch {
      /* blob may already be gone */
    }
    return;
  }
  try {
    await unlink(path.join(UPLOAD_DIR, path.basename(storedName)));
  } catch {
    /* local file may already be gone */
  }
}
