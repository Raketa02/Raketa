import type { Metadata } from 'next';

import { RaketaSettingsForm } from '@/features/raketa-settings/components/RaketaSettingsForm';
import { SETTINGS_COPY } from '@/features/raketa-settings/copy';
import { getSettingsPage } from '@/features/raketa-settings/queries';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: SETTINGS_COPY.title };

export default async function RaketaSettingsPage() {
  const { settings, confirmed } = await getSettingsPage();
  return (
    <>
      <PageHeader caption={SETTINGS_COPY.caption} title={SETTINGS_COPY.title} />
      <RaketaSettingsForm settings={settings} confirmed={confirmed} />
    </>
  );
}
