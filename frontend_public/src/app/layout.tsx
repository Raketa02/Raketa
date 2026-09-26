import '@fontsource/archivo/400.css';
import '@fontsource/archivo/700.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@/ui/tokens.css';
import '@/ui/base.css';

import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { SITE_COPY } from '@/ui/copy';

export const metadata: Metadata = {
  title: { default: SITE_COPY.name, template: `%s · ${SITE_COPY.name}` },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
