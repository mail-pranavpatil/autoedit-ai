/** @type {import('next').NextConfig} */

// When NEXT_PUBLIC_API_URL is empty the browser calls the API same-origin
// (/api/*, /health) and Next proxies to the FastAPI service below. Keeps the
// autoedit_session cookie same-site (required for the iOS WebView shell and for
// any cross-host deploy where *.onrender.com is a public suffix).
// Render's `fromService: hostport` yields a scheme-less "host:port" — add http://.
const RAW_API_PROXY_ORIGIN = process.env.API_PROXY_ORIGIN || "http://localhost:8000";
const API_PROXY_ORIGIN = /^https?:\/\//.test(RAW_API_PROXY_ORIGIN)
  ? RAW_API_PROXY_ORIGIN
  : `http://${RAW_API_PROXY_ORIGIN}`;

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API_PROXY_ORIGIN}/api/:path*` },
      { source: "/health", destination: `${API_PROXY_ORIGIN}/health` },
    ];
  },
};

module.exports = nextConfig;
