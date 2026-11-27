import '@fontsource-variable/archivo';
import '@fontsource/ibm-plex-mono/400.css';
import '@/ui/tokens.css';
import '@/ui/base.css';

import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { SITE_COPY } from '@/ui/copy';

export const metadata: Metadata = {
  title: { default: 'Rakieta for Clubs', template: '%s · Rakieta for Clubs' },
  description: SITE_COPY.description,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
