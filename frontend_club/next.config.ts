import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // `next dev` would append its own agent rules to CLAUDE.md, pointing at node_modules/, which
  // this app's settings deny reading. CLAUDE.md says where to find Next's docs instead.
  agentRules: false,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // A page with a password box is never drawn inside somebody else's frame.
          { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
        ],
      },
      {
        // The email's link carries its token in the path; nothing may send it on in a Referer.
        source: '/reset/:token*',
        headers: [{ key: 'Referrer-Policy', value: 'no-referrer' }],
      },
    ];
  },
};

export default nextConfig;
