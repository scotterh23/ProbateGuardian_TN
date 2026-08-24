-- AlterEnum
ALTER TYPE "VendorCategory" ADD VALUE 'OTHER';

-- AlterTable
ALTER TABLE "Estate" ADD COLUMN "listingUrl" TEXT,
ADD COLUMN "settlementUrl" TEXT,
ADD COLUMN "settlementFileName" TEXT,
ADD COLUMN "settlementFilePath" TEXT,
ADD COLUMN "settlementFileMime" TEXT;
