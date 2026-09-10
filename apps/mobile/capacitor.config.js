// CommonJS config (no TypeScript dependency needed for the Capacitor CLI).
//
// The shell loads the *hosted* web app directly (online-only, which AutoEdit AI
// already is). Point this at your single-origin deployment from Phase 0
// (Next.js serving the app + proxying /api/* and /health to FastAPI).

const SERVER_URL = process.env.AUTOEDIT_APP_URL || "https://REPLACE-with-your-domain.example";

/** @type {import('@capacitor/cli').CapacitorConfig} */
const config = {
  appId: "ai.autoedit.app",
  appName: "AutoEdit AI",
  webDir: "public",
  server: {
    url: SERVER_URL,
    cleartext: false,
  },
  ios: {
    contentInset: "always",
    limitsNavigationsToAppBoundDomains: false,
  },
};

module.exports = config;
