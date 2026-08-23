-- CreateTable
CREATE TABLE "EstateQuestion" (
    "id" TEXT NOT NULL,
    "estateId" TEXT NOT NULL,
    "authorId" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "EstateQuestion_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "EstateQuestion_estateId_createdAt_idx" ON "EstateQuestion"("estateId", "createdAt");

-- AddForeignKey
ALTER TABLE "EstateQuestion" ADD CONSTRAINT "EstateQuestion_estateId_fkey" FOREIGN KEY ("estateId") REFERENCES "Estate"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EstateQuestion" ADD CONSTRAINT "EstateQuestion_authorId_fkey" FOREIGN KEY ("authorId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
