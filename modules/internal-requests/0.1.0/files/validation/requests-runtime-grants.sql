GRANT SELECT ON app."InternalRequest" TO bpruntime;
GRANT INSERT ("id", "title", "description", "status", "ownerId", "createdAt", "updatedAt", "archivedAt", "version") ON app."InternalRequest" TO bpruntime;
GRANT UPDATE ("title", "description", "status", "updatedAt", "archivedAt", "version") ON app."InternalRequest" TO bpruntime;
