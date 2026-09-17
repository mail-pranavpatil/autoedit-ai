import { createClient } from "@supabase/supabase-js";

// Login/signup system of record. The anon key is a public, client-safe key
// by design (Supabase's own recommendation is to embed it in client apps) -
// the backend verifies tokens against Supabase's public JWKS endpoint, so
// there's no shared secret on either side anymore.
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://gxwungthmfdbtjnbbupm.supabase.co";
const SUPABASE_ANON_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd4d3VuZ3RobWZkYnRqbmJidXBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkzOTM5NjksImV4cCI6MjEwNDk2OTk2OX0.WCsC1bAfd5aMKz7nmAfgR__hbMk7uFONBbQeaKZm6EI";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
