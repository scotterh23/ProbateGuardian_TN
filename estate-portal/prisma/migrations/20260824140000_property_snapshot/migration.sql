-- CreateEnum
CREATE TYPE "TransactionStatus" AS ENUM ('INSPECTION', 'APPRAISAL', 'FINANCING', 'CLEAR_TO_CLOSE');

-- AlterTable
ALTER TABLE "Estate" ADD COLUMN "estimatedValue" INTEGER,
ADD COLUMN "listPrice" INTEGER,
ADD COLUMN "listingNotes" TEXT,
ADD COLUMN "contractPrice" INTEGER,
ADD COLUMN "transactionStatus" "TransactionStatus",
ADD COLUMN "salePrice" INTEGER,
ADD COLUMN "netToEstate" INTEGER,
ADD COLUMN "netNotes" TEXT;
