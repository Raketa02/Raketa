import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The FastAPI base URL is server-only: it is read by BFF route handlers and
  // Server Components, never shipped to the browser. Do NOT rename it to
  // NEXT_PUBLIC_* — the browser must only ever talk to this app's own /api/*.
  // See CLAUDE.md "Safety" and docs/adr/0007.
  eslint: {
    // CI runs `pnpm lint` as its own step; don't lint twice during build.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
