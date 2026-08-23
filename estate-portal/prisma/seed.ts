import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  if (process.env.ALLOW_SEED !== "true") {
    console.error(
      "Refusing to seed. Set ALLOW_SEED=true if you really want to wipe and reload demo data."
    );
    process.exit(1);
  }

  const passwordHash = await bcrypt.hash("demo1234", 10);

  await prisma.estateQuestion.deleteMany();
  await prisma.updateComment.deleteMany();
  await prisma.estateUpdate.deleteMany();
  await prisma.document.deleteMany();
  await prisma.invite.deleteMany();
  await prisma.estateMember.deleteMany();
  await prisma.estate.deleteMany();
  await prisma.user.deleteMany();

  const admin = await prisma.user.create({
    data: {
      email: "admin@probateguardians.com",
      name: "Scott Hardesty",
      role: "ADMIN",
      passwordHash,
    },
  });
  const executor = await prisma.user.create({
    data: {
      email: "executor@example.com",
      name: "Jane Whitfield",
      role: "EXECUTOR",
      passwordHash,
    },
  });
  const heir = await prisma.user.create({
    data: {
      email: "heir@example.com",
      name: "Michael Whitfield",
      role: "HEIR",
      passwordHash,
    },
  });
  const attorney = await prisma.user.create({
    data: {
      email: "attorney@example.com",
      name: "Patricia Cole, Esq.",
      role: "ATTORNEY",
      passwordHash,
    },
  });

  const estate = await prisma.estate.create({
    data: {
      nickname: "Whitfield family home",
      address: "4521 Main St",
      city: "Lebanon",
      county: "Wilson",
      status: "VALUATION",
    },
  });

  await prisma.estateMember.createMany({
    data: [
      { estateId: estate.id, userId: executor.id, role: "EXECUTOR" },
      { estateId: estate.id, userId: heir.id, role: "HEIR" },
      { estateId: estate.id, userId: attorney.id, role: "ATTORNEY" },
      { estateId: estate.id, userId: admin.id, role: "ADMIN" },
    ],
  });

  await prisma.estateUpdate.create({
    data: {
      estateId: estate.id,
      authorId: admin.id,
      body: "Walk-through completed this morning. House is vacant, lawn is current, and locks were changed. Photos are in the vault. Next step is a CMA / Net Sheet so the family can compare a traditional listing vs. an as-is path.",
    },
  });

  await prisma.estateQuestion.create({
    data: {
      estateId: estate.id,
      authorId: heir.id,
      body: "I live in Ohio and couldn’t get down this month. Can you confirm the locks were actually changed?",
    },
  });

  await prisma.estateUpdate.create({
    data: {
      estateId: estate.id,
      authorId: attorney.id,
      body: "Letters Testamentary were issued last week. No sale petition is required under the will, but any contract should still note that closing is subject to estate administration.",
    },
  });

  console.log("Seeded demo estate.");
  console.log("Logins (password for all: demo1234)");
  console.log("  Admin:     admin@probateguardians.com");
  console.log("  Executor:  executor@example.com");
  console.log("  Heir:      heir@example.com");
  console.log("  Attorney:  attorney@example.com");
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
