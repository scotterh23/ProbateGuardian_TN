import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const email = (process.env.ADMIN_EMAIL || "").trim().toLowerCase();
  const password = process.env.ADMIN_PASSWORD || "";
  const name = (process.env.ADMIN_NAME || "Scott Hardesty").trim();

  if (!email || !email.includes("@")) {
    console.error("Set ADMIN_EMAIL to the admin login email.");
    process.exit(1);
  }
  if (password.length < 10) {
    console.error("Set ADMIN_PASSWORD to a password of at least 10 characters.");
    process.exit(1);
  }

  const existingAdmin = await prisma.user.findFirst({ where: { role: "ADMIN" } });
  if (existingAdmin && process.env.FORCE_ADMIN !== "true") {
    console.error(
      `An admin already exists (${existingAdmin.email}). Refusing to create another.\n` +
        "If you intend to reset this account, rerun with FORCE_ADMIN=true (same email)."
    );
    process.exit(1);
  }

  const passwordHash = await bcrypt.hash(password, 12);
  const existing = await prisma.user.findUnique({ where: { email } });

  if (existing) {
    await prisma.user.update({
      where: { id: existing.id },
      data: { name, passwordHash, role: "ADMIN" },
    });
    console.log(`Updated existing user to admin: ${email}`);
  } else {
    await prisma.user.create({
      data: { email, name, passwordHash, role: "ADMIN" },
    });
    console.log(`Created first admin: ${email}`);
  }

  console.log("You can sign in on the live portal with that email and password.");
  console.log("This script does not print the password. Change it after first login if you shared it.");
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
