GRANT USAGE ON SCHEMA app TO bpruntime;
GRANT SELECT ON app."User", app."Account" TO bpruntime;
GRANT SELECT, INSERT, UPDATE, DELETE ON app."Session" TO bpruntime;
