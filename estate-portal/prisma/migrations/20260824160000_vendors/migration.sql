-- CreateEnum
CREATE TYPE "VendorCategory" AS ENUM (
  'ESTATE_SALE',
  'CLEAN_OUT',
  'LAWN',
  'LOCKSMITH',
  'CLEANING',
  'HANDYMAN',
  'APPRAISER',
  'CASH_ADVANCE'
);

-- CreateTable
CREATE TABLE "Vendor" (
    "id" TEXT NOT NULL,
    "category" "VendorCategory" NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "phone" TEXT,
    "email" TEXT,
    "serviceArea" TEXT,
    "notes" TEXT,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Vendor_pkey" PRIMARY KEY ("id")
);
