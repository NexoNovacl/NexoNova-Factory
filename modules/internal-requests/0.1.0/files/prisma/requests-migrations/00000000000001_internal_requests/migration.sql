-- app and auth are provisioned by the unchanged auth migration.
CREATE TYPE "app"."InternalRequestStatus" AS ENUM ('open', 'closed');
CREATE TABLE "app"."InternalRequest" (
  "id" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "status" "app"."InternalRequestStatus" NOT NULL DEFAULT 'open',
  "ownerId" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  "archivedAt" TIMESTAMP(3),
  "version" INTEGER NOT NULL DEFAULT 1,
  CONSTRAINT "InternalRequest_pkey" PRIMARY KEY ("id"),
  CONSTRAINT "InternalRequest_title_length" CHECK (char_length("title") BETWEEN 1 AND 120),
  CONSTRAINT "InternalRequest_description_length" CHECK (char_length("description") <= 2000),
  CONSTRAINT "InternalRequest_version_positive" CHECK ("version" >= 1),
  CONSTRAINT "InternalRequest_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "app"."User"("id") ON DELETE RESTRICT ON UPDATE RESTRICT
);
CREATE INDEX "InternalRequest_ownerId_idx" ON "app"."InternalRequest"("ownerId");
CREATE INDEX "InternalRequest_ownerId_archivedAt_createdAt_id_idx" ON "app"."InternalRequest"("ownerId", "archivedAt", "createdAt", "id");
CREATE INDEX "InternalRequest_archivedAt_createdAt_id_idx" ON "app"."InternalRequest"("archivedAt", "createdAt", "id");
