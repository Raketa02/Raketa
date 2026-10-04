import type { Metadata } from 'next';

import { Administrators } from '@/features/administrators/components/Administrators';
import { getAdministrators } from '@/features/administrators/queries';
import { SITE_COPY } from '@/ui/copy';

export const metadata: Metadata = { title: SITE_COPY.frame.pages.administrators };

export default async function AdministratorsPage() {
  return <Administrators administrators={await getAdministrators()} />;
}
