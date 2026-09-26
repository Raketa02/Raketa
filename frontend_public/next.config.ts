import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // `next dev` would append its own agent rules to CLAUDE.md, pointing at node_modules/, which
  // this app's settings deny reading. CLAUDE.md says where to find Next's docs instead.
  agentRules: false,
  // **Every client gets its preview tags in <head>** (ADR-0187 §4). Next may stream metadata into
  // the body for any user agent not on its list of limited bots, once a page sends its shell
  // before its metadata resolves, and a messenger missing from that list would then read a head
  // with no title, description or image. Today no page here has a loading boundary, and the group
  // page awaits the same read as its tags, so e2e/preview.spec.ts passes either way; this keeps it
  // so when a page grows one. Every page awaits its data anyway, so blocking costs nothing.
  htmlLimitedBots: /.*/,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          // A link here may carry a code or a token in its path; nothing may send it on in a
          // Referer (ADR-0187 §6).
          { key: 'Referrer-Policy', value: 'no-referrer' },
        ],
      },
    ];
  },
};

export default nextConfig;
